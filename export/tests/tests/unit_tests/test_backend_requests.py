#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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

import pytest
import requests
import requests_mock

from export_src.backend_requests import get_sensor_metadata, get_station_metadata_for, get_weather_data_for

URL = 'something'
PORT = 443

EXPECTED_METADATA = {
    'uv': {'description': 'UV', 'unit': 'UV-X'},
    'temperature': {'description': 'Temperatur', 'unit': '°C'},
}

SERVER_RESPONSE = [
    {'description': 'UV', 'sensor_id': 'uv', 'unit': 'UV-X'},
    {'description': 'Temperatur', 'sensor_id': 'temperature', 'unit': '°C'}]

STATION_SERVER_RESPONSE = [
    {'device': 'TE923', 'height': 520.0, 'id': 5, 'latitude': -20.23425, 'location': 'Test place/TE/LA',
     'longitude': 40.0234, 'rain_calib_factor': 0.6820802083333333, 'station_id': 'TES'},
    {'device': 'TE923', 'height': 3.5, 'id': 4, 'latitude': 30.3423, 'location': 'Test place 2/TE/LA',
     'longitude': 83.2342, 'rain_calib_factor': 0.6820802083333333, 'station_id': 'TEX'}]

EXPECTED_STATION_METADATA = STATION_SERVER_RESPONSE

WEATHER_DATA_SERVER_RESPONSE = {
    'TES': {
        'direction': [123.5, 345.4, 234.5],
        'gusts': [39.5, 45.9, 53.2],
        'timepoint': ['2021-11-01T00:00:00+01:00', '2021-11-01T00:10:00+01:00', '2021-11-01T00:20:00+01:00']
    }
}

EXPECTED_WEATHER_DATA = WEATHER_DATA_SERVER_RESPONSE


def test_get_sensor_metadata():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), json=SERVER_RESPONSE)
        metadata = get_sensor_metadata(URL, PORT)

    assert metadata == EXPECTED_METADATA


def test_get_sensor_metadata_when_timeout():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/sensor'.format(URL, PORT), exc=requests.exceptions.ConnectTimeout)
        with pytest.raises(requests.exceptions.ConnectTimeout):
            get_sensor_metadata(URL, PORT)


def test_get_station_metadata():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_SERVER_RESPONSE)
        metadata = get_station_metadata_for(URL, PORT)

    assert metadata == EXPECTED_STATION_METADATA


def test_get_station_metadata_for_one_station():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_SERVER_RESPONSE)
        metadata = get_station_metadata_for(URL, PORT, 'TES')

    assert isinstance(metadata, list)
    assert metadata == [EXPECTED_STATION_METADATA[0]]


def test_get_station_metadata_when_timeout():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/station'.format(URL, PORT), exc=requests.exceptions.ConnectTimeout)
        with pytest.raises(requests.exceptions.ConnectTimeout):
            get_station_metadata_for(URL, PORT)


def test_get_station_metadata_for_not_existing_station():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/station'.format(URL, PORT), json=STATION_SERVER_RESPONSE)
        with pytest.raises(ValueError):
            get_station_metadata_for(URL, PORT, 'ANY')


def test_get_weather_data_for():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/data'.format(URL, PORT), json=WEATHER_DATA_SERVER_RESPONSE)
        weather_data = get_weather_data_for(11, 2021, 'TES', URL, PORT)

    assert weather_data == EXPECTED_WEATHER_DATA


def test_get_weather_data_for_when_timeout():
    with requests_mock.Mocker() as m:
        m.get('https://{}:{}/api/v1/data'.format(URL, PORT), exc=requests.exceptions.ConnectTimeout)
        with pytest.raises(requests.exceptions.ConnectTimeout):
            get_weather_data_for(11, 2021, 'TES', URL, PORT)
