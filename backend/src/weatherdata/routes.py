from http import HTTPStatus

import pandas as pd
from flask import request, jsonify, current_app, Blueprint

from .schemas import time_period_with_sensors_schema, weather_dataset_schema, time_period_with_stations_schema
from ..exceptions import APIError
from ..extensions import db
from ..models import WeatherDataset, WindSensorData, TempHumiditySensorData
from ..sensor.models import Sensor
from ..utils import Role, with_rollback_and_raise_exception, approve_committed_station_ids
from ..utils import access_level_required, json_with_rollback_and_raise_exception

weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['PUT'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def add_or_update_weather_datasets():
    # TODO: this is not working with updating, generally solutions are only possible with Postgres or MySQL:
    # TODO: * variant 1 (manipulating the statement): https://stackoverflow.com/questions/25955200/sqlalchemy-performing-a-bulk-upsert-if-exists-update-else-insert-in-postgr
    # TODO: * variant 2 (using SQLAlchemy core): https://stackoverflow.com/questions/7165998/how-to-do-an-upsert-with-sqlalchemy
    # TODO:             https://gist.github.com/nirizr/9145aa27dd953bd73d11251d386fdbf1
    # TODO: variant 3: use this method only for POST which will reject any update, have a PUT method that takes dict of lists which are fast to read in pandas that can provide the required dicts for each table separately
    new_datasets = weather_dataset_schema.load(request.json, session=db.session)

    num_datasets_before_commit = WeatherDataset.query.count()
    db.session.add_all(new_datasets)
    station_ids_in_commit = [val[0] for val in db.session.query(WeatherDataset.station_id).distinct().all()]
    approve_committed_station_ids(station_ids_in_commit)
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
@access_level_required(Role.GUEST)
@json_with_rollback_and_raise_exception
def get_weather_datasets():
    time_period_with_sensors = time_period_with_sensors_schema.load(request.json)
    first = time_period_with_sensors['first_timepoint']
    last = time_period_with_sensors['last_timepoint']
    requested_sensors = time_period_with_sensors['sensors']  # TODO: validation using marshmallow-enum ...

    if len(requested_sensors) == 0:
        requested_sensors = [sensor[0] for sensor in db.session.query(Sensor).with_entities(Sensor.sensor_id).all()]

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
                                                                                   *requested_sensors).statement,
                                 db.session.bind)

    if found_datasets.empty:
        return jsonify({}), HTTPStatus.OK

    found_datasets_per_station, num_datasets_per_station = _reshape_datasets_to_dict(found_datasets, requested_sensors)

    num_datasets_log_str = ', '.join(num_datasets_per_station)
    response = jsonify(found_datasets_per_station)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned datasets from time period \'{}\'-\'{}\' ({})'.format(first, last,
                                                                                           num_datasets_log_str))

    return response


def _reshape_datasets_to_dict(found_datasets, requested_sensors):
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
                elif sensor_id in ['direction', 'gusts', 'speed', 'wind_temperature']:
                    found_datasets_per_station[station_id]['wind'][sensor_id] = data
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

    if 'direction' or 'gusts' or 'speed' or 'wind_temperature' in requested_sensors:
        station_dict['wind'] = {}

    return station_dict


@weatherdata_blueprint.route('', methods=['DELETE'])
@access_level_required(Role.ADMIN)
@json_with_rollback_and_raise_exception
def delete_weather_dataset():
    time_period_with_stations = time_period_with_stations_schema.load(request.json)
    first = time_period_with_stations['first_timepoint']
    last = time_period_with_stations['last_timepoint']
    stations = time_period_with_stations['stations']  # TODO: validation using marshmallow-enum ...

    # TODO: this is unnecessary with Postgres
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
@access_level_required(Role.GUEST)
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
