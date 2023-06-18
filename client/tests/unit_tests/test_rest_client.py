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
import json
import os
from datetime import datetime
from gzip import decompress
from unittest import mock

import pytest
import requests
import requests_mock

from client_src.rest_client import ServerProxy
from client_src.utils import IsoDateTimeJSONDecoder
from .common import CONNECT_TIMEOUT_IN_MIN, WRITE_TIMEOUT_IN_MIN, CONFIG
from ..common import USER_NAME, URL, PORT, PASSWORD, TOKEN, LOGIN_RESPONSE

STATION_ID = 'TES'

JSON_DATA = [
    {
        'timepoint': datetime(2021, 4, 24, 21, 30),
        'station_id': 'TES',
        'pressure': 1010.6,
        'uv': None,
        'rain_counter': 2120,
        'speed': None,
        'gusts': None,
        'direction': None,
        'wind_temperature': None,
        'temperature_humidity': [
            {'sensor_id': 'OUT1', 'temperature': 1.9, 'humidity': 48.0},
            {'sensor_id': 'IN', 'temperature': 29.62, 'humidity': 16.0}
        ]
    },
    {
        'timepoint': datetime(2021, 4, 24, 21, 40),
        'station_id': 'TES',
        'pressure': 1025.9,
        'uv': None,
        'rain_counter': 2121,
        'speed': None,
        'gusts': None,
        'direction': None,
        'wind_temperature': None,
        'temperature_humidity': [
            {'sensor_id': 'OUT1', 'temperature': 12.69, 'humidity': 18.0},
            {'sensor_id': 'IN', 'temperature': 26.55, 'humidity': 54.0}
        ]
    }
]


@pytest.fixture()
def client_env_variables():
    with mock.patch.dict(os.environ, {'BACKEND_PASSWORD': PASSWORD}):
        yield


def test_send_data(client_env_variables):
    with requests_mock.Mocker() as m:
        login_post = m.post('https://{}:{}/api/v1/login'.format(URL, PORT), json=LOGIN_RESPONSE)
        data_post = m.post('https://{}:{}/api/v1/data'.format(URL, PORT))

        proxy = ServerProxy(CONFIG)
        proxy.send_data(JSON_DATA, STATION_ID)

        assert login_post.called_once
        assert login_post.last_request.json() == {'name': USER_NAME, 'password': PASSWORD}

        assert data_post.called_once
        got_json_data = json.loads(decompress(data_post.last_request.body).decode('utf-8'), cls=IsoDateTimeJSONDecoder)
        assert JSON_DATA == got_json_data
        assert data_post.last_request.timeout == (CONNECT_TIMEOUT_IN_MIN * 60, WRITE_TIMEOUT_IN_MIN * 60)
        assert data_post.last_request.headers['Content-Encoding'] == 'gzip'
        assert data_post.last_request.headers['Content-Type'] == 'application/json'
        assert data_post.last_request.headers['Authorization'] == f'Bearer {TOKEN}'


def test_empty_data(client_env_variables):
    with requests_mock.Mocker() as m:
        login_post = m.post('https://{}:{}/api/v1/login'.format(URL, PORT), json=LOGIN_RESPONSE)
        data_post = m.post('https://{}:{}/api/v1/data'.format(URL, PORT))

        proxy = ServerProxy(CONFIG)
        proxy.send_data({}, STATION_ID)

        assert not login_post.called
        assert not data_post.called


# noinspection HttpUrlsUsage
def test_send_data_without_required_re_login(client_env_variables):
    with requests_mock.Mocker() as m:
        login_post = m.post('http://{}:{}/api/v1/login'.format(URL, PORT), json=LOGIN_RESPONSE)
        data_post = m.post('http://{}:{}/api/v1/data'.format(URL, PORT))

        config = dict(CONFIG)
        config['use_ssl'] = False

        proxy = ServerProxy(config)
        proxy.send_data(JSON_DATA, STATION_ID)
        proxy.send_data(JSON_DATA, STATION_ID)  # does not require a new login

        assert login_post.call_count == 1
        assert data_post.call_count == 2


def test_send_data_without_backend_password():
    with pytest.raises(ValueError):
        ServerProxy(CONFIG)


def test_send_data_with_connection_error_on_login(client_env_variables):
    with requests_mock.Mocker() as m:
        login_post = m.post('https://{}:{}/api/v1/login'.format(URL, PORT), status_code=500)
        data_post = m.post('https://{}:{}/api/v1/data'.format(URL, PORT))

        with pytest.raises(requests.exceptions.HTTPError):
            proxy = ServerProxy(CONFIG)
            proxy.send_data(JSON_DATA, STATION_ID)

        assert login_post.called_once
        assert not data_post.called


def test_send_data_with_connection_error_on_data_post(client_env_variables):
    with requests_mock.Mocker() as m:
        login_post = m.post('https://{}:{}/api/v1/login'.format(URL, PORT), json=LOGIN_RESPONSE)
        data_post = m.post('https://{}:{}/api/v1/data'.format(URL, PORT), status_code=500)

        with pytest.raises(requests.exceptions.HTTPError):
            proxy = ServerProxy(CONFIG)
            proxy.send_data(JSON_DATA, STATION_ID)

        assert login_post.called_once
        assert data_post.called_once
