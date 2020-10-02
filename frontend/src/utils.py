#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
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

import math
from datetime import datetime, timedelta

import dateutil.parser
from requests.adapters import HTTPAdapter

HUMID_SENSOR_MARKER = '_humid'
TEMP_SENSOR_MARKER = '_temp'


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            raise SyntaxError('Timeout parameter is missing')
        self._timeout = kwargs['timeout']
        del kwargs['timeout']
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = self._timeout
        return super().send(request, **kwargs)


def is_temp_sensor(sensor_id):
    return sensor_id.endswith(TEMP_SENSOR_MARKER)


def is_humidity_sensor(sensor_id):
    return sensor_id.endswith(HUMID_SENSOR_MARKER)


def _get_temp_humidity_sensor_id(sensor_id):
    return sensor_id.split('_')[0]


def get_sensor_data(data, station_id, sensor_id):
    if is_temp_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['temperature']
    elif is_humidity_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['humidity']
    else:
        sensor_data = data[station_id][sensor_id]
    return sensor_data


def floor_to_n(val, n):
    return math.floor(val / n) * n


def ceil_to_n(val, n):
    return math.ceil(val / n) * n


def determine_start_and_end_dates(start_time_str, end_time_str):
    if start_time_str is not None:
        actual_start_time = dateutil.parser.parse(start_time_str)
        start_date = datetime(actual_start_time.year, actual_start_time.month, actual_start_time.day)
    else:
        start_date = None

    if end_time_str is not None:
        actual_end_time = dateutil.parser.parse(end_time_str)
        end_date = datetime(actual_end_time.year, actual_end_time.month, actual_end_time.day) + timedelta(days=1)
    else:
        end_date = None

    return start_date, end_date


def update_bounded_index(index, index_list):
    index += 1
    if index >= len(index_list):
        index = 0
    return index


def convert_input_into_lists(chosen_sensors, chosen_stations):
    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]

    if isinstance(chosen_sensors, str):
        chosen_sensors = [chosen_sensors]

    return chosen_sensors, chosen_stations


def get_current_date(time_zone):
    return datetime.now(time_zone).date()
