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
import signal
import time
from gzip import decompress
from http import HTTPStatus
from threading import Thread
from unittest import mock

import pytest
import requests_mock
from fastapi.testclient import TestClient

from client_main import main
from client_src.utils import IsoDateTimeJSONDecoder
from ..common import USER_NAME, URL, PORT, DATA_DIR, TOKEN, PASSWORD, LOGIN_RESPONSE, EXPECTED_DATA_FOR_SINGLE_TIMEPOINT

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), r'test_client_config.yaml')
WEATHER_DATA_READER_FILE_PATH = os.path.join(os.path.dirname(__file__), r'../weather_station_mock/te923con_mock.py')

TEST_RUNTIME_IN_SEC = 70  # must be adapted to the mock weather station read interval


@pytest.fixture(autouse=True)
def client_env_variables():
    with mock.patch.dict(os.environ, {'BACKEND_PASSWORD': PASSWORD}):
        yield


def termination_thread_func():
    time.sleep(TEST_RUNTIME_IN_SEC)
    os.kill(os.getpid(), signal.SIGTERM)


def call_healthcheck_func(client):
    time.sleep(TEST_RUNTIME_IN_SEC / 2)
    response = client.get('/healthcheck')

    # we do not know if data has already been read from the mock weather station
    assert response.status_code == HTTPStatus.OK or response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_main(monkeypatch, tmp_path_factory):
    with requests_mock.Mocker() as m:
        login_post = m.post('https://{}:{}/api/v1/login'.format(URL, PORT), json=LOGIN_RESPONSE)
        data_post = m.post('https://{}:{}/api/v1/data'.format(URL, PORT))
        from client_main import app

        client = TestClient(app)

        data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

        monkeypatch.setattr('sys.argv',
                            ['main',
                             f'--config-file={CONFIG_FILE_PATH}',
                             f'--data-dir={data_dir_path}',
                             f'--weather-data-reader-file={WEATHER_DATA_READER_FILE_PATH}'])

        termination_thread = Thread(target=termination_thread_func)
        termination_thread.start()

        call_healthcheck_thread = Thread(target=call_healthcheck_func, args=(client,))
        call_healthcheck_thread.start()

        main()

        assert login_post.called
        assert login_post.last_request.json() == {'name': USER_NAME, 'password': PASSWORD}

        got_json_data = json.loads(decompress(data_post.last_request.body).decode('utf-8'),
                                   cls=IsoDateTimeJSONDecoder)[0]
        del got_json_data['timepoint']

        assert data_post.called
        assert got_json_data == EXPECTED_DATA_FOR_SINGLE_TIMEPOINT
        assert data_post.last_request.headers['Content-Encoding'] == 'gzip'
        assert data_post.last_request.headers['Content-Type'] == 'application/json'
        assert data_post.last_request.headers['Authorization'] == f'Bearer {TOKEN}'

        termination_thread.join()
        call_healthcheck_thread.join()
