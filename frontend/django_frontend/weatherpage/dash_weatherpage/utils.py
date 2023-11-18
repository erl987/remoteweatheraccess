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

from datetime import datetime, timedelta
from enum import Enum
from math import floor, ceil

from dateutil.parser import parse
from numpy import nan
from requests.adapters import HTTPAdapter

HUMID_SENSOR_MARKER = '_humid'
TEMP_SENSOR_MARKER = '_temp'
DEWPOINT_SENSOR_MARKER = '_dewpoint'


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


def is_dewpoint_sensor(sensor_id):
    return sensor_id.endswith(DEWPOINT_SENSOR_MARKER)


def _get_temp_humidity_sensor_id(sensor_id):
    return sensor_id.split('_')[0]


def _is_temp_humidity_sensor(sensor_id):
    if is_temp_sensor(sensor_id):
        return True
    elif is_humidity_sensor(sensor_id):
        return True
    elif is_dewpoint_sensor(sensor_id):
        return True
    else:
        return False


def get_sensor_data(data, station_id, sensor_id):
    if (_is_temp_humidity_sensor(sensor_id) and
            _get_temp_humidity_sensor_id(sensor_id) not in data[station_id]['temperature_humidity']):
        return []

    if is_temp_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['temperature']
    elif is_humidity_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['humidity']
    elif is_dewpoint_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['dewpoint']
    else:
        sensor_data = data[station_id][sensor_id]

    sensor_data_with_nans = [nan if x is None else x for x in sensor_data]  # the data from the backend contains None

    return sensor_data_with_nans


def floor_to_n(val, n):
    return floor(val / n) * n


def ceil_to_n(val, n):
    return ceil(val / n) * n


def determine_start_and_end_dates(start_time_str, end_time_str):
    if start_time_str is not None:
        actual_start_time = parse(start_time_str)
        start_date = datetime(actual_start_time.year, actual_start_time.month, actual_start_time.day)
    else:
        start_date = None

    if end_time_str is not None:
        actual_end_time = parse(end_time_str)
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


def get_url_encoded_iso_time_string(time: datetime):
    # this function is able to handle times that contain timezone information
    return time.isoformat().replace('+', '%2b')


class BootstrapBreakpoint(Enum):
    XS = 0
    SM = 1
    MD = 2
    LG = 3
    XL = 4
    XXL = 5


def is_at_least_bootstrap_breakpoint(breakpoint_name: str, bootstrap_breakpoint: BootstrapBreakpoint) -> bool:
    return (BREAKPOINT_WIDTH_IN_PX[BootstrapBreakpoint[breakpoint_name.upper()]]
            >= BREAKPOINT_WIDTH_IN_PX[bootstrap_breakpoint])


# https://getbootstrap.com/docs/5.0/layout/breakpoints/
BREAKPOINT_WIDTH_IN_PX = {
    BootstrapBreakpoint.XS: 0,
    BootstrapBreakpoint.SM: 576,
    BootstrapBreakpoint.MD: 768,
    BootstrapBreakpoint.LG: 992,
    BootstrapBreakpoint.XL: 1200,
    BootstrapBreakpoint.XXL: 1400,
}


def backend_uses_https():
    from os import environ

    if environ['BACKEND_DO_USE_HTTPS'].lower().strip().startswith('true'):
        backend_do_use_https = True
    else:
        backend_do_use_https = False

    return backend_do_use_https
