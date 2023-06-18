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
import datetime
import os
from unittest import mock

import pytest
import pytz

from client_src.station_interface import WeatherStationProxy, LastKnownStationData
from .common import CONFIG, A_LOCAL_TIME_POINT
from ..common import DATA_DIR, EXPECTED_DATA_FOR_SINGLE_TIMEPOINT

WEATHER_DATA_READER_PATH = r'../weather_station_mock/te923con_mock.py'
WEATHER_DATA_READER_THAT_HANGS_PATH = r'../weather_station_mock/te923con_mock_that_hangs.py'
WEATHER_DATA_READER_THAT_FAILS_PATH = r'../weather_station_mock/te923con_mock_that_fails.py'

EXPECTED_DATA_FOR_FIRST_TIMEPOINT = {
    'timepoint': pytz.timezone('Europe/Berlin').localize(datetime.datetime(2021, 4, 24, 21, 30)),
    'station_id': 'TES',
    'pressure': 1010.6,
    'uv': None,
    'rain_counter': 2120,
    'speed': None, 'gusts': None,
    'direction': None,
    'wind_temperature': None,
    'temperature_humidity': [
        {'sensor_id': 'OUT1', 'temperature': 1.9, 'humidity': 48.0},
        {'sensor_id': 'IN', 'temperature': 29.62, 'humidity': 16.0}
    ]
}


def get_send_data_call_args(server_proxy_mock):
    for call in server_proxy_mock.mock_calls:
        if call[0] == '().send_data':
            sent_json_data = call.args[0]
            sent_station_id = call.args[1]
            return sent_json_data, sent_station_id

    return None, None


@pytest.fixture()
def tz_env_variable():
    with mock.patch.dict(os.environ, {'TZ': 'Europe/Berlin'}):
        yield


@pytest.fixture(autouse=True)
def before_each_test():
    LastKnownStationData._instance = None
    yield


class TestWeatherStationProxy:
    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send_with_automatic_choice(self, server_proxy_mock, tz_env_variable,
                                                                       tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_PATH)

        proxy = WeatherStationProxy(CONFIG, data_dir_path, full_weather_data_reader_path)
        has_read_all_datasets = proxy.read_and_send_with_automatic_choice()
        sent_json_data, sent_station_id = get_send_data_call_args(server_proxy_mock)

        assert has_read_all_datasets

        assert sent_json_data is not None
        assert sent_station_id is not None
        assert len(sent_json_data) == 204
        assert sent_json_data[0] == EXPECTED_DATA_FOR_FIRST_TIMEPOINT
        assert sent_station_id == 'TES'

    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send(self, server_proxy_mock, tz_env_variable, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_PATH)

        proxy = WeatherStationProxy(CONFIG, data_dir_path, full_weather_data_reader_path)
        has_read_data = proxy.read_and_send(do_read_all_datasets=False)
        sent_json_data, sent_station_id = get_send_data_call_args(server_proxy_mock)

        assert has_read_data

        assert len(sent_json_data) == 1
        utc_now = datetime.datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=pytz.UTC)
        sent_time_point = sent_json_data[0]['timepoint']
        assert utc_now - sent_time_point < datetime.timedelta(
            seconds=10)  # allow for some offset to avoid false positives
        del sent_json_data[0]['timepoint']
        assert sent_json_data[0] == EXPECTED_DATA_FOR_SINGLE_TIMEPOINT

        assert sent_station_id == 'TES'

    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send_when_hanging(self, _, tz_env_variable, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_THAT_HANGS_PATH)

        config = dict(CONFIG)
        config['timeouts_in_min']['latest_dataset_read'] = 3 / 60

        proxy = WeatherStationProxy(config, data_dir_path, full_weather_data_reader_path)

        with pytest.raises(ConnectionError):
            proxy.read_and_send(False)

    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send_when_receiving_error(self, _, tz_env_variable, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_THAT_FAILS_PATH)

        proxy = WeatherStationProxy(CONFIG, data_dir_path, full_weather_data_reader_path)

        with pytest.raises(ConnectionError):
            proxy.read_and_send(False)

    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send_with_automatic_choice_twice(self, _, tz_env_variable,
                                                                             tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_PATH)

        proxy = WeatherStationProxy(CONFIG, data_dir_path, full_weather_data_reader_path)
        has_read_all_datasets = proxy.read_and_send_with_automatic_choice()
        assert has_read_all_datasets is True

        has_read_all_datasets = proxy.read_and_send_with_automatic_choice()
        assert has_read_all_datasets is True

    @mock.patch('client_src.station_interface.ServerProxy')
    def test_weather_station_proxy_read_and_send_twice(self, _, tz_env_variable, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
        full_weather_data_reader_path = os.path.join(os.path.dirname(__file__), WEATHER_DATA_READER_PATH)

        proxy = WeatherStationProxy(CONFIG, data_dir_path, full_weather_data_reader_path)
        has_new_data = proxy.read_and_send(True)
        assert has_new_data is True

        has_new_data = proxy.read_and_send(True)
        assert has_new_data is False


class TestLastKnownStationData:
    def test_last_known_station_data_get_utc_time_point(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        datetime_min_utc = datetime.datetime.min.replace(tzinfo=pytz.UTC)
        assert LastKnownStationData.get(data_dir_path).get_utc_time_point() == datetime_min_utc

    def test_last_known_station_data_set_utc_time_point(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        LastKnownStationData.get(data_dir_path).set_utc_time_point(A_LOCAL_TIME_POINT)

        assert A_LOCAL_TIME_POINT == LastKnownStationData.get(data_dir_path).get_utc_time_point()
        assert LastKnownStationData.get(data_dir_path).get_utc_time_point().tzinfo == pytz.UTC

    def test_last_known_station_data_get_utc_time_point_when_cached_file_exists(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        LastKnownStationData.get(data_dir_path).set_utc_time_point(A_LOCAL_TIME_POINT)

        LastKnownStationData._instance = None  # triggers reloading of the singleton

        assert A_LOCAL_TIME_POINT == LastKnownStationData.get(data_dir_path).get_utc_time_point()
        assert LastKnownStationData.get(data_dir_path).get_utc_time_point().tzinfo == pytz.UTC

    def test_last_known_station_data_get_utc_time_point_when_corrupt_data_file_exists(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        LastKnownStationData.get(data_dir_path).set_utc_time_point(A_LOCAL_TIME_POINT)
        LastKnownStationData.get(data_dir_path).set_utc_time_point(A_LOCAL_TIME_POINT)  # creating backup file

        # truncate the last character in the JSON file to make it corrupt
        with open(os.path.join(data_dir_path, LastKnownStationData.DATA_FILE), 'rb+') as file:
            file.seek(-1, 2)
            file.truncate()

        LastKnownStationData._instance = None  # triggers reloading of the singleton

        assert A_LOCAL_TIME_POINT == LastKnownStationData.get(data_dir_path).get_utc_time_point()
        assert LastKnownStationData.get(data_dir_path).get_utc_time_point().tzinfo == pytz.UTC

    def test_last_known_station_data_get_when_backup_file_is_missing(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        LastKnownStationData.get(data_dir_path).set_utc_time_point(A_LOCAL_TIME_POINT)  # no backup file is yet created

        # truncate the last character in the JSON file to make it corrupt
        with open(os.path.join(data_dir_path, LastKnownStationData.DATA_FILE), 'rb+') as file:
            file.seek(-1, 2)
            file.truncate()

        LastKnownStationData._instance = None  # triggers reload of the singleton

        with pytest.raises(FileNotFoundError):
            LastKnownStationData.get(data_dir_path)

    def test_initialize_singleton_two_times(self, tmp_path_factory):
        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        LastKnownStationData(data_dir_path)
        with pytest.raises(AssertionError):
            LastKnownStationData(data_dir_path)
