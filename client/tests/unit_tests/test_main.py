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
import os
from datetime import datetime, timedelta
from http import HTTPStatus

import pytest
import pytz
from fastapi.testclient import TestClient

from client_main import EndpointSettings, load_config_file
from client_src.station_interface import LastKnownStationData
from ..common import DATA_DIR

UNHEALTHY_AFTER_THIS_TIME_WITHOUT_TRANSFER = 2.0
ACCEPTABLE_MINUTES_BEFORE_CURR_TIME = 1
TOO_MANY_MINUTES_BEFORE_CURR_TIME = 2.05

INVALID_CONFIG_FILE_PATH = r'test_client_config_invalid.yaml'
CONFIG_FILE_PATH = r'../integration_tests/test_client_config.yaml'


@pytest.fixture(autouse=True)
def before_each_test():
    LastKnownStationData._instance = None
    yield


def test_health_check_when_healthy(tmp_path_factory):
    import client_main
    from client_main import app

    client = TestClient(app)

    an_acceptable_last_time_point = (datetime.utcnow().replace(tzinfo=pytz.UTC) -
                                     timedelta(minutes=ACCEPTABLE_MINUTES_BEFORE_CURR_TIME))

    data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
    LastKnownStationData.get(data_dir_path).set_utc_time_point(an_acceptable_last_time_point)
    client_main.endpoint_settings = EndpointSettings(data_dir_path,
                                                     UNHEALTHY_AFTER_THIS_TIME_WITHOUT_TRANSFER)

    response = client.get('/healthcheck')
    assert response.status_code == HTTPStatus.OK


def test_health_check_when_unhealthy(tmp_path_factory):
    import client_main
    from client_main import app

    client = TestClient(app)

    a_too_early_last_time_point = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(
        minutes=TOO_MANY_MINUTES_BEFORE_CURR_TIME)

    data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))
    LastKnownStationData.get(data_dir_path).set_utc_time_point(a_too_early_last_time_point)
    client_main.endpoint_settings = EndpointSettings(data_dir_path,
                                                     UNHEALTHY_AFTER_THIS_TIME_WITHOUT_TRANSFER)

    response = client.get('/healthcheck')
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_health_check_when_internal_server_error(tmp_path_factory):
    import client_main
    from client_main import app

    client = TestClient(app)

    data_dir_path = str(tmp_path_factory.mktemp(DATA_DIR))

    # noinspection PyTypeChecker
    client_main.endpoint_settings = EndpointSettings(data_dir_path, 'an_invalid_string')

    response = client.get('/healthcheck')
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_load_config_file():
    full_config_file_path = os.path.join(os.path.dirname(__file__), CONFIG_FILE_PATH)
    _, config_file_is_not_present, config_file_path = load_config_file(full_config_file_path)

    assert config_file_is_not_present is False
    assert config_file_path == full_config_file_path


def test_load_config_file_with_syntax_error():
    with pytest.raises(SyntaxError):
        load_config_file(os.path.join(os.path.dirname(__file__), INVALID_CONFIG_FILE_PATH))
