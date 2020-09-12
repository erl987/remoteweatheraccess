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

from datetime import datetime

from frontend.src.utils import determine_start_and_end_dates, update_bounded_index, convert_input_into_lists
from frontend.src.utils import floor_to_n, ceil_to_n, get_sensor_data

SOME_PORT = 80
SOME_URL = 'http://something'

A_STATION_ID = 'TES'
A_SENSOR_ID = 'pressure'

A_TEMP_HUMIDITY_SENSOR_ID = 'IN'

A_FIRST_TIMPOINT = '2020-01-01T20:00:00'
A_LAST_TIMEPOINT = '2020-01-01T23:15:00'

EXPECTED_SENSOR_DATA = [1013.0, 1015.1, 1014.2]
EXPECTED_TEMP_SENSOR_DATA = [10.5, 9.4, 8.3, 8.6]
EXPECTED_HUMIDITY_SENSOR_DATA = [80.4, 70.5, 59.1, 65.2]


def _get_some_sensor_data():
    sensor_data = {
        A_STATION_ID: {
            A_SENSOR_ID: EXPECTED_SENSOR_DATA,
            'temperature_humidity': {
                A_TEMP_HUMIDITY_SENSOR_ID: {
                    'temperature': EXPECTED_TEMP_SENSOR_DATA,
                    'humidity': EXPECTED_HUMIDITY_SENSOR_DATA
                }
            }
        }
    }
    return sensor_data


def test_floor_to_n():
    floored_val = floor_to_n(14.2, 5)
    assert floored_val == 10


def test_floor_to_n_for_negative_number():
    floored_val = floor_to_n(-14.2, 5)
    assert floored_val == -15


def test_ceil_to_n():
    ceiled_val = ceil_to_n(14.2, 5)
    assert ceiled_val == 15


def test_ceil_to_n_for_negative_number():
    ceiled_val = ceil_to_n(-14.2, 5)
    assert ceiled_val == -10


def test_get_sensor_data():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, A_SENSOR_ID)
    assert got_sensor_data == EXPECTED_SENSOR_DATA


def test_get_sensor_data_for_temperature():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, '{}_temp'.format(A_TEMP_HUMIDITY_SENSOR_ID))
    assert got_sensor_data == EXPECTED_TEMP_SENSOR_DATA


def test_get_sensor_data_for_humidity():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, '{}_humid'.format(A_TEMP_HUMIDITY_SENSOR_ID))
    assert got_sensor_data == EXPECTED_HUMIDITY_SENSOR_DATA


def test_get_start_and_end_times():
    start_date, end_date = determine_start_and_end_dates(A_FIRST_TIMPOINT, A_LAST_TIMEPOINT)
    assert start_date == datetime(year=2020, month=1, day=1)
    assert end_date == datetime(year=2020, month=1, day=2)


def test_get_start_and_end_times_when_none():
    start_date, end_date = determine_start_and_end_dates(None, None)
    assert start_date is None
    assert end_date is None


def test_update_bounded_index():
    index_list = [0, 1, 2, 3, 4]
    assert update_bounded_index(3, index_list) == 4
    assert update_bounded_index(4, index_list) == 0


def test_convert_input_into_lists():
    a_string_for_sensor_id_list = 'a string'
    a_string_for_station_list = 'another string'
    assert convert_input_into_lists(a_string_for_sensor_id_list, a_string_for_station_list) == \
           ([a_string_for_sensor_id_list], [a_string_for_station_list])
    assert convert_input_into_lists([a_string_for_sensor_id_list], [a_string_for_station_list]) == \
           ([a_string_for_sensor_id_list], [a_string_for_station_list])
