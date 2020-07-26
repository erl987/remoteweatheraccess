from http import HTTPStatus

import pandas as pd
from flask import request, jsonify, current_app, Blueprint

from .models import WeatherDataset, WindSensorData, TempHumiditySensorData
from .schemas import time_period_with_sensors_schema, weather_dataset_schema, time_period_with_stations_schema
from ..exceptions import APIError
from ..extensions import db
from ..utils import Role, with_rollback_and_raise_exception
from ..utils import access_level_required, json_with_rollback_and_raise_exception

weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['PUT'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def add_or_update_weather_datasets():
    # TODO: this is not working with updating, maybe an option is to use this (works only with Postgres): https://stackoverflow.com/questions/25955200/sqlalchemy-performing-a-bulk-upsert-if-exists-update-else-insert-in-postgr
    new_datasets = weather_dataset_schema.load(request.json, session=db.session)

    num_datasets_before_commit = WeatherDataset.query.count()
    db.session.add_all(new_datasets)
    db.session.commit()
    num_datasets_after_commit = WeatherDataset.query.count()
    num_new_datasets = num_datasets_after_commit - num_datasets_before_commit

    response = jsonify(new_datasets)
    current_app.logger.info('Committed {} datasets to the database, this are {} new entries'
                            .format(len(new_datasets), num_new_datasets))

    if num_new_datasets > 0:
        response.status_code = HTTPStatus.CREATED
    else:
        response.status_code = HTTPStatus.OK

    return response


@weatherdata_blueprint.route('', methods=['GET'])
@json_with_rollback_and_raise_exception
def get_weather_datasets():
    time_period_with_sensors = time_period_with_sensors_schema.load(request.json)
    first = time_period_with_sensors['first_timepoint']
    last = time_period_with_sensors['last_timepoint']
    requested_sensors = time_period_with_sensors['sensors']  # TODO: validation using marshmallow-enum ...

    requested_base_station_sensors, requested_entities, requested_temp_humidity_sensors, requested_wind_sensors = \
        _create_query_configuration(requested_sensors)

    if last < first:
        raise APIError('Last time \'{}\' is later than first time \'{}\''.format(last, first),
                       status_code=HTTPStatus.BAD_REQUEST)

    found_datasets = pd.read_sql(db.session.query(WeatherDataset)
                                 .filter(WeatherDataset.timepoint >= first)
                                 .filter(WeatherDataset.timepoint <= last)
                                 .join(WeatherDataset.wind)
                                 .join(WeatherDataset.temperature_humidity)
                                 .order_by(WeatherDataset.timepoint).with_entities(WeatherDataset.timepoint,
                                                                                   WeatherDataset.station_id,
                                                                                   TempHumiditySensorData.sensor_id,
                                                                                   *requested_entities)
                                 .statement,
                                 db.session.bind)

    if found_datasets.empty:
        return jsonify({}), HTTPStatus.OK

    found_datasets_per_station = _create_get_response_payload(found_datasets, requested_base_station_sensors,
                                                              requested_temp_humidity_sensors, requested_wind_sensors)

    num_datasets_per_station = []
    for station_id, dataset in found_datasets_per_station.items():
        num_datasets_per_station.append('{}: {}'.format(station_id, len(dataset['timepoint'])))
    num_datasets_log_str = ', '.join(num_datasets_per_station)

    response = jsonify(found_datasets_per_station)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned datasets from time period \'{}\'-\'{}\' ({})'.format(first, last,
                                                                                           num_datasets_log_str))

    return response


def _create_get_response_payload(found_datasets, requested_base_station_sensors, requested_temp_humidity_sensors,
                                 requested_wind_sensors):
    combi_sensor_ids = found_datasets.sensor_id.unique()

    found_datasets_per_station = {}
    station_ids = found_datasets['station_id'].unique()
    for station_id in station_ids:
        station_datasets = found_datasets.loc[(found_datasets.station_id == station_id) &
                                              (found_datasets.sensor_id == 'IN')]

        found_datasets_per_station[station_id] = \
            station_datasets.loc[:, requested_base_station_sensors].to_dict('list')
        if len(requested_wind_sensors) > 0:
            found_datasets_per_station[station_id]['wind'] = \
                station_datasets.loc[:, requested_wind_sensors].to_dict('list')
        if len(requested_temp_humidity_sensors) > 0:
            found_datasets_per_station[station_id]['temperature_humidity'] = {}
            for combi_sensor_id in combi_sensor_ids:
                found_datasets_per_station[station_id]['temperature_humidity'][combi_sensor_id] = (
                    found_datasets.loc[(found_datasets.station_id == station_id) &
                                       (found_datasets.sensor_id == combi_sensor_id), requested_temp_humidity_sensors]
                        .to_dict('list'))
    return found_datasets_per_station


def _create_query_configuration(requested_sensors):
    do_configure_all = (len(requested_sensors) == 0)
    requested_base_station_sensors, requested_entities = _create_base_station_query_configuration(requested_sensors,
                                                                                                  do_configure_all)
    requested_wind_sensors = _create_wind_sensor_query_configuration(requested_entities, requested_sensors,
                                                                     do_configure_all)
    requested_temp_humidity_sensors = _create_temp_humidity_sensor_query_configuration(requested_entities,
                                                                                       requested_sensors,
                                                                                       do_configure_all)

    return requested_base_station_sensors, requested_entities, requested_temp_humidity_sensors, requested_wind_sensors


def _create_temp_humidity_sensor_query_configuration(requested_entities, requested_sensors, do_configure_all):
    requested_entities.extend([TempHumiditySensorData.temperature, TempHumiditySensorData.humidity])
    requested_temp_humidity_sensors = ['temperature', 'humidity']

    if not do_configure_all:
        if 'temperature' not in requested_sensors:
            requested_temp_humidity_sensors.remove('temperature')
            requested_entities.remove(TempHumiditySensorData.temperature)
        if 'humidity' not in requested_sensors:
            requested_temp_humidity_sensors.remove('humidity')
            requested_entities.remove(TempHumiditySensorData.humidity)

    return requested_temp_humidity_sensors


def _create_wind_sensor_query_configuration(requested_entities, requested_sensors, do_configure_all):
    requested_entities.extend(
        [WindSensorData.gusts, WindSensorData.direction, WindSensorData.wind_temperature, WindSensorData.speed])
    requested_wind_sensors = ['gusts', 'direction', 'wind_temperature', 'speed']

    if not do_configure_all:
        if 'gusts' not in requested_sensors:
            requested_wind_sensors.remove('gusts')
            requested_entities.remove(WindSensorData.gusts)
        if 'direction' not in requested_sensors:
            requested_wind_sensors.remove('direction')
            requested_entities.remove(WindSensorData.direction)
        if 'wind_temperature' not in requested_sensors:
            requested_wind_sensors.remove('wind_temperature')
            requested_entities.remove(WindSensorData.wind_temperature)
        if 'speed' not in requested_sensors:
            requested_wind_sensors.remove('speed')
            requested_entities.remove(WindSensorData.speed)

    return requested_wind_sensors


def _create_base_station_query_configuration(requested_sensors, do_configure_all):
    requested_entities = [WeatherDataset.pressure, WeatherDataset.uv, WeatherDataset.rain_counter]
    requested_base_station_sensors = ['timepoint', 'pressure', 'uv', 'rain_counter']

    if not do_configure_all:
        if 'pressure' not in requested_sensors:
            requested_base_station_sensors.remove('pressure')
            requested_entities.remove(WeatherDataset.pressure)
        if 'uv' not in requested_sensors:
            requested_base_station_sensors.remove('uv')
            requested_entities.remove(WeatherDataset.uv)
        if 'rain_counter' not in requested_sensors:
            requested_base_station_sensors.remove('rain_counter')
            requested_entities.remove(WeatherDataset.rain_counter)

    return requested_base_station_sensors, requested_entities


@weatherdata_blueprint.route('', methods=['DELETE'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def delete_weather_dataset():
    time_period_with_stations = time_period_with_stations_schema.load(request.json)
    first = time_period_with_stations['first_timepoint']
    last = time_period_with_stations['last_timepoint']
    stations = time_period_with_stations['stations']  # TODO: validation using marshmallow-enum ...

    # cascade deletion of multiple tables is not supported by the SQLite backend of SQLAlchemy
    _delete_datasets_from_table(TempHumiditySensorData, first, last, stations)
    _delete_datasets_from_table(WindSensorData, first, last, stations)
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
@with_rollback_and_raise_exception
def get_available_time_period():
    min_max_query_result = db.session.query(db.func.min(WeatherDataset.timepoint).label('min_time'),
                                            db.func.max(WeatherDataset.timepoint).label('max_time')).one()
    first_timepoint = min_max_query_result.min_time
    last_timepoint = min_max_query_result.max_time

    if not first_timepoint or not last_timepoint:
        raise APIError('No data in the database', status_code=HTTPStatus.NOT_FOUND)

    time_range = {
        'first_timepoint': first_timepoint,
        'last_timepoint': last_timepoint
    }

    response = jsonify(time_range)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range['first_timepoint'],
                                                                                   time_range['last_timepoint']))

    return response
