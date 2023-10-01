#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import gzip
import json
from datetime import timedelta
from http import HTTPStatus
from typing import List

import numpy as np
import pandas as pd
from flask import request, jsonify, current_app, Blueprint
from sqlalchemy import column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import Tuple

from .schemas import single_weather_dataset_schema, time_period_with_sensors_and_stations_schema, \
    latest_time_point_schema
from .schemas import time_period_with_stations_schema, many_weather_datasets_schema
from ..exceptions import APIError
from ..extensions import db
from ..models import WeatherDataset, TempHumiditySensorData, WeatherStation
from ..sensor.models import Sensor
from ..utils import Role, with_rollback_and_raise_exception, approve_committed_station_ids, validate_items, \
    calc_dewpoint
from ..utils import access_level_required, json_with_rollback_and_raise_exception, LocalTimeZone

weatherdata_blueprint = Blueprint('data', __name__, url_prefix='/api/v1/data')


@weatherdata_blueprint.route('', methods=['POST'])
@access_level_required(Role.PUSH_USER)
@json_with_rollback_and_raise_exception
def add_weather_datasets():
    num_ignored_datasets = 0

    if request.content_encoding == 'gzip':
        uncompressed_data = gzip.decompress(request.data)
    else:
        uncompressed_data = request.data
    json_data = json.loads(uncompressed_data)
    all_datasets = many_weather_datasets_schema.load(json_data, session=db.session)
    _add_timezone_to_datasets_if_required(all_datasets)

    try:
        _perform_add_datasets(all_datasets)
    except IntegrityError:
        num_ignored_datasets = _add_new_datasets_only(all_datasets)

    log_message = 'Added {} datasets to the database'.format(len(all_datasets) - num_ignored_datasets)
    if num_ignored_datasets > 0:
        log_message += ', ignored {} already existing datasets'.format(num_ignored_datasets)
    current_app.logger.info(log_message)

    return '', HTTPStatus.NO_CONTENT


def _add_new_datasets_only(all_datasets):
    # existing datasets are ignored in the POST-request
    db.session.rollback()

    keys_to_add = [(dataset.timepoint, dataset.station_id) for dataset in all_datasets]
    existing_datasets = WeatherDataset.query.filter(Tuple(WeatherDataset.timepoint, WeatherDataset.station_id)
                                                    .in_(keys_to_add)).all()
    existing_keys = [(dataset.timepoint, dataset.station_id) for dataset in existing_datasets]

    new_datasets = [x for x in all_datasets if (x.timepoint, x.station_id) not in existing_keys]
    num_ignored_datasets = len(all_datasets) - len(new_datasets)

    # ambiguous time points can occur on shift from summer to winter time - in this case only the earlier time point
    # of each duplicate is considered
    _, unique_indices = np.unique([x.timepoint for x in new_datasets], return_index=True)
    new_unique_datasets = np.array(new_datasets)[unique_indices]
    if len(new_unique_datasets) != len(new_datasets):
        current_app.logger.info('{} duplicate time points are present in the dataset, they have been filtered out'
                                .format(len(new_datasets) - len(new_unique_datasets)))

    _perform_add_datasets(new_unique_datasets)

    return num_ignored_datasets


def _add_timezone_to_datasets_if_required(all_datasets):
    for dataset in all_datasets:
        if not dataset.timepoint.tzinfo:
            dataset.timepoint = LocalTimeZone.get(current_app).get_local_time_zone().localize(dataset.timepoint)


def _perform_add_datasets(all_datasets):
    db.session.add_all(all_datasets)
    station_ids_in_commit = set([dataset.station_id for dataset in all_datasets])
    approve_committed_station_ids(station_ids_in_commit)
    db.session.commit()


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
@with_rollback_and_raise_exception
def get_weather_datasets():
    first, last, requested_sensors, requested_stations = _get_query_params()

    found_datasets_per_station, num_datasets_per_station = _perform_get_weather_datasets(first, last, requested_sensors,
                                                                                         requested_stations)

    num_datasets_log_str = ', '.join(num_datasets_per_station)
    response = jsonify(found_datasets_per_station)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned datasets from time period \'{}\'-\'{}\' ({})'.format(first, last,
                                                                                           num_datasets_log_str))

    return response


def _perform_get_weather_datasets(first, last, requested_sensors, requested_stations):
    requested_sensors = _get_requested_sensors(requested_sensors)
    queried_sensors = _get_queried_sensors(requested_sensors)
    requested_stations, rain_calib_factors = _get_requested_stations(requested_stations)
    found_datasets = _read_weather_data_from_db(first, last, queried_sensors, requested_stations)

    if found_datasets.empty:
        found_datasets_per_station = {}
        num_datasets_per_station = ['0']
    else:
        found_datasets_per_station, num_datasets_per_station = _reshape_datasets_to_dict(found_datasets,
                                                                                         requested_sensors,
                                                                                         rain_calib_factors)

    return found_datasets_per_station, num_datasets_per_station


def _get_requested_stations(requested_stations):
    all_stations_data = db.session.query(WeatherStation).with_entities(WeatherStation.station_id,
                                                                       WeatherStation.rain_calib_factor).all()
    all_stations = [station_data[0] for station_data in all_stations_data]

    rain_calib_factors = {station_data[0]: station_data[1] for station_data in all_stations_data}
    validate_items(requested_stations, all_stations, 'station')

    if len(requested_stations) == 0:
        requested_stations = all_stations

    return requested_stations, rain_calib_factors


def _get_requested_sensors(requested_sensors):
    all_sensors = [sensor[0] for sensor in db.session.query(Sensor).with_entities(Sensor.sensor_id).all()]
    validate_items(requested_sensors, all_sensors, 'sensor')

    if len(requested_sensors) == 0:
        requested_sensors = all_sensors

    return requested_sensors


def _read_weather_data_from_db(first, last, queried_sensors, requested_stations):
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
                                 db.engines['weather-data'])

    # required to provide standard conformant JSON containing `null` and not `NaN`
    found_datasets = found_datasets.replace([np.nan], [None])

    return found_datasets


def _get_query_params():
    time_period_with_sensors = time_period_with_sensors_and_stations_schema.load(_obtain_request_args_for_get_method())
    first = time_period_with_sensors['first_timepoint']
    last = time_period_with_sensors['last_timepoint']

    # times without given timezone are assumed to be given in server time zone
    if not first.tzinfo:
        first = LocalTimeZone.get(current_app).get_local_time_zone().localize(first)
    if not last.tzinfo:
        last = LocalTimeZone.get(current_app).get_local_time_zone().localize(last)

    requested_sensors = time_period_with_sensors['sensors']
    requested_stations = time_period_with_sensors['stations']

    return first, last, requested_sensors, requested_stations


def _obtain_request_args_for_get_method():
    request_args = dict(request.args.to_dict())

    if 'sensors' not in request_args:
        request_args['sensors'] = []
    else:
        request_args['sensors'] = _get_param_list_from_str(request_args['sensors'])

    if 'stations' not in request_args:
        request_args['stations'] = []
    else:
        request_args['stations'] = _get_param_list_from_str(request_args['stations'])

    return request_args


def _get_param_list_from_str(string):
    return list(set(filter(None, string.split(','))))


def _get_queried_sensors(requested_sensors) -> List[column]:
    queried_sensors = set(requested_sensors)
    rain_sensor_is_queried = False

    if 'rain' in queried_sensors:
        queried_sensors.remove('rain')
        rain_sensor_is_queried = True
    if 'rain_rate' in queried_sensors:
        queried_sensors.remove('rain_rate')
        rain_sensor_is_queried = True
    if rain_sensor_is_queried:
        queried_sensors.add('rain_counter')

    if 'dewpoint' in queried_sensors:
        queried_sensors.remove('dewpoint')
        queried_sensors.add('temperature')
        queried_sensors.add('humidity')

    queried_sensors = [column(sensor) for sensor in queried_sensors]

    return queried_sensors


def _reshape_datasets_to_dict(found_datasets, requested_sensors, rain_calib_factors):
    found_datasets['timepoint'] = (pd.to_datetime(found_datasets['timepoint'], utc=True).dt
                                   .tz_convert(current_app.config['TIMEZONE']))

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
                    _reshape_rain(found_datasets_per_station, requested_sensors, dataset, rain_calib_factors,
                                  station_id)
                else:
                    found_datasets_per_station[station_id][sensor_id] = data

    if 'dewpoint' in requested_sensors:
        _reshape_dewpoint(found_datasets_per_station, requested_sensors)

    num_datasets_per_station = []
    for station_id, dataset in found_datasets_per_station.items():
        num_datasets_per_station.append('{}: {}'.format(station_id, len(dataset['timepoint'])))

    return found_datasets_per_station, num_datasets_per_station


def _reshape_dewpoint(found_datasets_per_station, requested_sensors):
    for station_id in found_datasets_per_station:
        for temp_humidity_sensor_id in found_datasets_per_station[station_id]['temperature_humidity']:
            temp_humid_data = found_datasets_per_station[station_id]['temperature_humidity'][temp_humidity_sensor_id]
            dew_points = calc_dewpoint(temp_humid_data['temperature'], temp_humid_data['humidity'])
            temp_humid_data['dewpoint'] = dew_points
            if 'temperature' not in requested_sensors:
                del temp_humid_data['temperature']
            if 'humidity' not in requested_sensors:
                del temp_humid_data['humidity']


def _reshape_rain(found_datasets_per_station, requested_sensors, dataset, rain_calib_factors, station_id):
    rain_rate = dataset[1].diff() * rain_calib_factors[station_id]

    # handle reset of the rain counter to 0 due to battery replacement, etc.
    rain_rate = rain_rate.clip(lower=0)
    rain_rate.iloc[0] = 0

    if 'rain_rate' in requested_sensors:
        found_datasets_per_station[station_id]['rain_rate'] = rain_rate.to_list()
    if 'rain' in requested_sensors:
        found_datasets_per_station[station_id]['rain'] = rain_rate.cumsum().to_list()


def _create_station_dict(requested_sensors, temp_humidity_sensor_ids):
    station_dict = {}

    if not {'temperature', 'humidity', 'dewpoint'}.isdisjoint(requested_sensors):
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
    first_timepoint, last_timepoint = _get_first_and_last_time_point()

    time_range = {
        'first_timepoint': first_timepoint,
        'last_timepoint': last_timepoint
    }

    response = jsonify(time_range)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned available time period: \'{}\'-\'{}\''.format(time_range['first_timepoint'],
                                                                                   time_range['last_timepoint']))

    return response


def _get_first_and_last_time_point():
    min_max_query_result = db.session.query(db.func.min(WeatherDataset.timepoint).label('min_time'),
                                            db.func.max(WeatherDataset.timepoint).label('max_time')).one()
    first_time_point = min_max_query_result.min_time
    last_time_point = min_max_query_result.max_time
    return first_time_point, last_time_point


def _get_last_time_point_for_station(station_id):
    result = (db.session.query(db.func.max(WeatherDataset.timepoint).label('max_time'))
              .filter_by(station_id=station_id).one())
    last_time_point = result.max_time
    return last_time_point


@weatherdata_blueprint.route('/latest', methods=['GET'])
@access_level_required(Role.GUEST)
@with_rollback_and_raise_exception
def get_latest_data():
    station_id = latest_time_point_schema.load(request.args.to_dict())['station']

    last_time_point = _get_last_time_point_for_station(station_id)

    if not last_time_point:
        return jsonify({}), HTTPStatus.OK

    first_time_point = last_time_point - timedelta(hours=25)
    found_datasets_per_station, _ = _perform_get_weather_datasets(first_time_point,
                                                                  last_time_point,
                                                                  [],  # all
                                                                  [station_id])

    if len(found_datasets_per_station) == 0:
        raise APIError('Did not find any dataset when requesting the latest data')

    latest_dataset = _get_latest_dataset(found_datasets_per_station[station_id])

    response = jsonify(latest_dataset)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Returned latest data ({})'.format(last_time_point))

    return response


def _get_latest_dataset(found_datasets):
    latest_dataset = {}

    for sensor_id, entry in found_datasets.items():
        if sensor_id == 'temperature_humidity':
            if 'temperature_humidity' not in latest_dataset:
                latest_dataset['temperature_humidity'] = {}

            for temp_humid_sensor_id, temp_humid_entry in entry.items():
                if temp_humid_sensor_id not in latest_dataset['temperature_humidity']:
                    latest_dataset['temperature_humidity'][temp_humid_sensor_id] = {}

                for temp_humid_quantity_id, temp_humid_quantity_entry in temp_humid_entry.items():
                    latest_dataset[sensor_id][temp_humid_sensor_id][temp_humid_quantity_id] = \
                        temp_humid_quantity_entry[-1]
        else:
            latest_dataset[sensor_id] = entry[-1]

    rain_last_day, rain_last_hour = _get_rain_data(found_datasets)
    latest_dataset['rain_last_hour'] = rain_last_hour
    latest_dataset['rain_last_day'] = rain_last_day
    del latest_dataset['rain']
    del latest_dataset['rain_rate']

    return latest_dataset


def _get_rain_data(found_datasets):
    one_hour_index = _get_index_for_time_period_before_latest(1, found_datasets)
    one_day_index = _get_index_for_time_period_before_latest(24, found_datasets)

    if one_hour_index is not None:
        rain_last_hour = found_datasets['rain'][-1] - found_datasets['rain'][one_hour_index]
    else:
        rain_last_hour = None
    if one_day_index is not None:
        rain_last_day = found_datasets['rain'][-1] - found_datasets['rain'][one_day_index]
    else:
        rain_last_day = None

    return rain_last_day, rain_last_hour


def _get_index_for_time_period_before_latest(time_period_in_hours, found_datasets):
    timepoints = found_datasets['timepoint']
    latest_time_point = timepoints[-1]

    upper_accepted_limit = np.array((latest_time_point - pd.Series(timepoints))
                                    .ge(pd.Timedelta(hours=time_period_in_hours * 0.9)))
    if len(np.argwhere(upper_accepted_limit)) > 0:
        upper_accepted_limit_index = np.argwhere(upper_accepted_limit)[-1][0]
    else:
        upper_accepted_limit_index = None

    lower_accepted_limit = np.array((latest_time_point - pd.Series(timepoints))
                                    .le(pd.Timedelta(hours=time_period_in_hours + 1)))
    if len(np.argwhere(lower_accepted_limit)) > 0:
        lower_accepted_limit_index = np.argwhere(lower_accepted_limit)[0][0]
    else:
        lower_accepted_limit_index = None

    one_hour_index = np.nanmax(upper_accepted_limit_index, lower_accepted_limit_index)

    return one_hour_index
