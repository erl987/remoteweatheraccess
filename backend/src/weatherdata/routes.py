import gzip
import json
from http import HTTPStatus

import pandas as pd
from flask import request, jsonify, current_app, Blueprint

from .schemas import single_weather_dataset_schema, time_period_with_sensors_and_stations_schema, \
    many_weather_datasets_schema
from .schemas import time_period_with_stations_schema
from ..exceptions import APIError
from ..extensions import db
from ..models import WeatherDataset, TempHumiditySensorData, WeatherStation
from ..sensor.models import Sensor
from ..utils import Role, with_rollback_and_raise_exception, approve_committed_station_ids, validate_items
from ..utils import access_level_required, json_with_rollback_and_raise_exception

weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['POST'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def add_weather_datasets():
    if request.content_encoding == 'gzip':
        uncompressed_data = gzip.decompress(request.data)
    else:
        uncompressed_data = request.data
    json_data = json.loads(uncompressed_data)
    new_datasets = many_weather_datasets_schema.load(json_data, session=db.session)

    db.session.add_all(new_datasets)
    station_ids_in_commit = [val[0] for val in db.session.query(WeatherDataset.station_id).distinct().all()]
    approve_committed_station_ids(station_ids_in_commit)
    db.session.commit()

    current_app.logger.info('Added {} datasets to the database'.format(len(new_datasets)))
    return '', HTTPStatus.NO_CONTENT


@weatherdata_blueprint.route('', methods=['PUT'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def update_weather_dataset():
    new_dataset = single_weather_dataset_schema.load(request.json, session=db.session)

    approve_committed_station_ids([new_dataset.station_id])

    existing_dataset = WeatherDataset.query.filter(
        WeatherDataset.timepoint == new_dataset.timepoint and
        WeatherDataset.station_id == new_dataset.station_id
    ).one_or_none()

    if not existing_dataset:
        raise APIError('No dataset for station \'{}\' at timepoint \'{}\''.format(
            new_dataset.station_id,
            new_dataset.timepoint
        ), status_code=HTTPStatus.NOT_FOUND)

    existing_dataset.pressure = new_dataset.pressure
    existing_dataset.uv = new_dataset.uv
    existing_dataset.rain_count = new_dataset.rain_counter

    for index, existing_sensor_data in enumerate(existing_dataset.temperature_humidity):
        existing_sensor_id = existing_sensor_data.sensor_id

        sensors_matched = False
        for new_sensor_data in new_dataset.temperature_humidity:
            if new_sensor_data.sensor_id == existing_sensor_id:
                existing_sensor_data.temperature = new_sensor_data.temperature
                existing_sensor_data.humidity = new_sensor_data.humidity
                sensors_matched = True
                break

        if not sensors_matched:
            raise APIError('No matching temperature humidity sensor found for sensor id \'{}\''
                           .format(existing_sensor_id), status_code=HTTPStatus.NOT_FOUND)

    existing_dataset.direction = new_dataset.direction
    existing_dataset.speed = new_dataset.speed
    existing_dataset.wind_temperature = new_dataset.wind_temperature
    existing_dataset.gusts = new_dataset.gusts

    db.session.commit()

    current_app.logger.info('Updated data for station \'{}\' at timepoint \'{}\''
                            .format(existing_dataset.station_id, existing_dataset.timepoint))

    return '', HTTPStatus.NO_CONTENT


@weatherdata_blueprint.route('', methods=['GET'])
@access_level_required(Role.GUEST)
@json_with_rollback_and_raise_exception
def get_weather_datasets():
    time_period_with_sensors = time_period_with_sensors_and_stations_schema.load(request.json)
    first = time_period_with_sensors['first_timepoint']
    last = time_period_with_sensors['last_timepoint']
    requested_sensors = time_period_with_sensors['sensors']
    requested_stations = time_period_with_sensors['stations']

    all_sensors = [sensor[0] for sensor in db.session.query(Sensor).with_entities(Sensor.sensor_id).all()]
    validate_items(requested_sensors, all_sensors, 'sensor')

    if len(requested_sensors) == 0:
        requested_sensors = all_sensors

    queried_sensors = _get_queried_sensors(requested_sensors)

    all_stations_data = db.session.query(WeatherStation).with_entities(WeatherStation.station_id,
                                                                       WeatherStation.rain_calib_factor).all()
    all_stations = [station_data[0] for station_data in all_stations_data]
    rain_calib_factors = {station_data[0]: station_data[1] for station_data in all_stations_data}
    validate_items(requested_stations, all_stations, 'station')

    if len(requested_stations) == 0:
        requested_stations = all_stations

    if last < first:
        raise APIError('Last time \'{}\' is later than first time \'{}\''.format(last, first),
                       status_code=HTTPStatus.BAD_REQUEST)

    found_datasets = pd.read_sql(db.session.query(WeatherDataset)
                                 .filter(WeatherDataset.timepoint >= first)
                                 .filter(WeatherDataset.timepoint <= last)
                                 .filter(WeatherDataset.station_id.in_(requested_stations))
                                 .join(WeatherDataset.temperature_humidity)
                                 .order_by(WeatherDataset.timepoint).with_entities(WeatherDataset.timepoint,
                                                                                   WeatherDataset.station_id,
                                                                                   TempHumiditySensorData.sensor_id,
                                                                                   *queried_sensors).statement,
                                 db.get_engine(current_app, 'weather-data'))

    if found_datasets.empty:
        return jsonify({}), HTTPStatus.OK

    found_datasets_per_station, num_datasets_per_station = _reshape_datasets_to_dict(found_datasets, requested_sensors,
                                                                                     rain_calib_factors)

    num_datasets_log_str = ', '.join(num_datasets_per_station)
    response = jsonify(found_datasets_per_station)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned datasets from time period \'{}\'-\'{}\' ({})'.format(first, last,
                                                                                           num_datasets_log_str))

    return response


def _get_queried_sensors(requested_sensors):
    queried_sensors = list(requested_sensors)
    rain_sensor_is_queried = False

    if 'rain' in queried_sensors:
        queried_sensors.remove('rain')
        rain_sensor_is_queried = True
    if 'rain_rate' in queried_sensors:
        queried_sensors.remove('rain_rate')
        rain_sensor_is_queried = True
    if rain_sensor_is_queried:
        queried_sensors.append('rain_counter')

    return queried_sensors


def _reshape_datasets_to_dict(found_datasets, requested_sensors, rain_calib_factors):
    found_datasets['timepoint'] = found_datasets['timepoint'].dt.tz_convert(current_app.config['TIMEZONE'])

    found_datasets_per_station = {}
    temp_humidity_sensor_ids = found_datasets.sensor_id.unique()
    grouped_datasets = found_datasets.groupby(['station_id', 'sensor_id'])

    for sensor_id in list(found_datasets.columns):
        if sensor_id not in ['station_id', 'sensor_id']:
            for dataset in grouped_datasets[sensor_id]:
                station_id = dataset[0][0]
                temp_humidity_sensor = dataset[0][1]
                data = dataset[1].to_list()

                if station_id not in found_datasets_per_station:
                    found_datasets_per_station[station_id] = _create_station_dict(requested_sensors,
                                                                                  temp_humidity_sensor_ids)

                if sensor_id in ['temperature', 'humidity']:
                    found_datasets_per_station[station_id]['temperature_humidity'][temp_humidity_sensor][
                        sensor_id] = data
                elif sensor_id in ['rain_counter']:
                    rain_rate = dataset[1].diff() * rain_calib_factors[station_id]
                    rain_rate.iloc[0] = 0
                    if 'rain_rate' in requested_sensors:
                        found_datasets_per_station[station_id]['rain_rate'] = rain_rate.to_list()
                    if 'rain' in requested_sensors:
                        found_datasets_per_station[station_id]['rain'] = rain_rate.cumsum().to_list()
                else:
                    found_datasets_per_station[station_id][sensor_id] = data

    num_datasets_per_station = []
    for station_id, dataset in found_datasets_per_station.items():
        num_datasets_per_station.append('{}: {}'.format(station_id, len(dataset['timepoint'])))

    return found_datasets_per_station, num_datasets_per_station


def _create_station_dict(requested_sensors, temp_humidity_sensor_ids):
    station_dict = {}

    if 'temperature' or 'humidity' in requested_sensors:
        station_dict['temperature_humidity'] = {}
        for temp_humidity_sensor_id in temp_humidity_sensor_ids:
            station_dict['temperature_humidity'][temp_humidity_sensor_id] = {}

    return station_dict


@weatherdata_blueprint.route('', methods=['DELETE'])
@access_level_required(Role.ADMIN)
@json_with_rollback_and_raise_exception
def delete_weather_dataset():
    time_period_with_stations = time_period_with_stations_schema.load(request.json)
    first = time_period_with_stations['first_timepoint']
    last = time_period_with_stations['last_timepoint']
    stations = time_period_with_stations['stations']

    all_stations = [sensor[0] for sensor in
                    db.session.query(WeatherStation).with_entities(WeatherStation.station_id).all()]
    validate_items(stations, all_stations, 'station')

    _delete_datasets_from_table(TempHumiditySensorData, first, last, stations)
    num_deleted_datasets = _delete_datasets_from_table(WeatherDataset, first, last, stations)

    db.session.commit()

    if len(stations) == 0:
        station_log_str = 'all stations'
    else:
        station_log_str = 'the stations [' + ', '.join(stations) + ']'

    current_app.logger.info('Deleted {} dataset(s) within time period \'{}\'-\'{}\' for {} from the database'
                            .format(num_deleted_datasets, first, last, station_log_str))
    return '', HTTPStatus.NO_CONTENT


def _delete_datasets_from_table(table, first_timepoint, last_timepoint, stations):
    query = (db.session.query(table)
             .filter(table.timepoint >= first_timepoint)
             .filter(table.timepoint < last_timepoint))

    if len(stations) > 0:
        query = query.filter(table.station_id.in_(stations))
    return query.delete(synchronize_session=False)


@weatherdata_blueprint.route('/limits', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_available_time_period():
    min_max_query_result = db.session.query(db.func.min(WeatherDataset.timepoint).label('min_time'),
                                            db.func.max(WeatherDataset.timepoint).label('max_time')).one()
    first_timepoint = min_max_query_result.min_time
    last_timepoint = min_max_query_result.max_time

    time_range = {
        'first_timepoint': first_timepoint,
        'last_timepoint': last_timepoint
    }

    response = jsonify(time_range)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range['first_timepoint'],
                                                                                   time_range['last_timepoint']))

    return response
