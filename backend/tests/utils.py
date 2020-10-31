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

import gzip
import json
import logging
from http import HTTPStatus
from io import BytesIO

import pytest
from flask_jwt_extended import create_access_token

from backend_app import create_app, IsoDateTimeJSONEncoder
from backend_config.settings import TestConfig
from backend_src.extensions import db
from backend_src.models import WeatherStation, create_temp_humidity_sensors, create_sensors
from backend_src.utils import Role


@pytest.fixture
def a_dataset() -> dict:
    yield [{
        'timepoint': '2016-02-05T15:40:36.078357+01:00',
        'station_id': 'TES',
        'pressure': 1020.5,
        'uv': 9.6,
        'rain_counter': 980.5,
        'direction': 190.5,
        'speed': 95.2,
        'wind_temperature': 9.8,
        'gusts': 120.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 10.5,
            'humidity': 90.5
        }]
    }]


@pytest.fixture
def an_updated_dataset() -> dict:
    yield {
        'timepoint': '2016-02-05T15:40:36.078357+01:00',
        'station_id': 'TES',
        'pressure': 1035.2,
        'uv': 7.2,
        'rain_counter': 920.6,
        'direction': 310.5,
        'speed': 85.3,
        'wind_temperature': 9.8,
        'gusts': 80.3,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 30.9,
            'humidity': 90.5
        }]
    }


@pytest.fixture
def another_dataset() -> dict:
    yield [{
        'timepoint': '2016-02-06T15:40:36.2Z',
        'station_id': 'TES',
        'pressure': 1019.2,
        'uv': 2.4,
        'rain_counter': 980.5,
        'direction': 350.2,
        'speed': 95.2,
        'wind_temperature': 9.8,
        'gusts': 120.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 23.5,
            'humidity': 53.0
        }]
    }]


@pytest.fixture
def another_dataset_without_timezone() -> dict:
    yield [{
        'timepoint': '2016-02-06T16:40:36.2',
        'station_id': 'TES',
        'pressure': 1019.2,
        'uv': 2.4,
        'rain_counter': 980.5,
        'direction': 350.2,
        'speed': 95.2,
        'wind_temperature': 9.8,
        'gusts': 120.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 23.5,
            'humidity': 53.0
        }]
    }]


@pytest.fixture
def a_dataset_for_another_station() -> dict:
    yield [{
        'timepoint': '2016-02-06T15:40:36.2Z',
        'station_id': 'TES2',
        'pressure': 1019.2,
        'uv': 2.4,
        'rain_counter': 980.5,
        'direction': 350.2,
        'speed': 95.2,
        'wind_temperature': 9.8,
        'gusts': 120.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 23.5,
            'humidity': 53.0
        }]
    }]


@pytest.fixture
def a_user() -> dict:
    yield {
        'name': 'test_user',
        'password': 'd5df93*!B',
        'role': 'PUSH_USER',
        'station_id': 'TES'
    }


@pytest.fixture
def an_updated_user() -> dict:
    yield {
        'name': 'test_user',
        'password': 'updated_pw',
        'role': 'ADMIN',
        'station_id': 'TES'
    }


@pytest.fixture
def another_user() -> dict:
    yield {
        'name': 'test_user_2',
        'password': 'bdfdfd53*!B',
        'role': 'PULL_USER',
        'station_id': 'TES'
    }


@pytest.fixture()
def a_station() -> dict:
    yield {
        'station_id': 'TES3',
        'device': 'DEVICE3',
        'latitude': -25.05,
        'longitude': -2.5,
        'location': 'The Location 3',
        'height': -2.5,
        'rain_calib_factor': 0.9
    }


@pytest.fixture()
def an_updated_station() -> dict:
    yield {
        'station_id': 'TES3',
        'device': 'DEVICE3',
        'latitude': 35.3,
        'longitude': 39.5,
        'location': 'The Location 3 Updated',
        'height': 19.3,
        'rain_calib_factor': 1.5
    }


@pytest.fixture()
def another_station() -> dict:
    yield {
        'station_id': 'TES4',
        'device': 'DEVICE4',
        'latitude': -25.05,
        'longitude': -2.5,
        'location': 'The Location 4',
        'height': -2.5,
        'rain_calib_factor': 0.9
    }


@pytest.fixture
def client_without_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_stations()
        _create_sensors()

    try:
        yield client
    finally:
        with app.test_request_context():
            db.drop_all()


@pytest.fixture
def client_with_push_user_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_stations()
        _create_sensors()
        admin_access_token = create_access_token(identity={'name': 'pytest_user'},
                                                 user_claims={'role': Role.PUSH_USER.name, 'station_id': 'TES'},
                                                 expires_delta=False,
                                                 fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    try:
        yield client
    finally:
        with app.test_request_context():
            db.drop_all()


@pytest.fixture
def client_with_admin_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_stations()
        _create_sensors()
        admin_access_token = create_access_token(identity={'name': 'pytest_admin'},
                                                 user_claims={'role': Role.ADMIN.name, 'station_id': None},
                                                 expires_delta=False,
                                                 fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    try:
        yield client
    finally:
        with app.test_request_context():
            db.drop_all()


def _create_mock_weather_stations():
    db.create_all()

    test_weather_station = WeatherStation()
    test_weather_station.station_id = 'TES'
    test_weather_station.device = 'DEVICE'
    test_weather_station.latitude = -25.05
    test_weather_station.longitude = -2.5
    test_weather_station.location = 'The Location'
    test_weather_station.height = -2.5
    test_weather_station.rain_calib_factor = 0.9
    db.session.add(test_weather_station)

    test_weather_station = WeatherStation()
    test_weather_station.station_id = 'TES2'
    test_weather_station.device = 'DEVICE2'
    test_weather_station.latitude = 93.5
    test_weather_station.longitude = 20.3
    test_weather_station.location = 'The Location 2'
    test_weather_station.height = 203.5
    test_weather_station.rain_calib_factor = 1.1
    db.session.add(test_weather_station)

    db.session.commit()


def _create_sensors():
    create_temp_humidity_sensors()
    create_sensors()


def drop_permissions(client):
    del client.environ_base['HTTP_AUTHORIZATION']
    return client


def drop_registration_details_for_user(user):
    del user['station_id']
    del user['role']


def verify_database_is_empty(client_with_admin_permissions):
    client = drop_permissions(client_with_admin_permissions)
    check_result = client.get('/api/v1/data/limits')
    assert not check_result.get_json()['first_timepoint']
    assert not check_result.get_json()['last_timepoint']


def zip_payload(object_payload) -> bytes:
    json_payload = json.dumps(object_payload, cls=IsoDateTimeJSONEncoder)
    byte_stream = BytesIO()
    with gzip.GzipFile(fileobj=byte_stream, mode='w') as g:
        g.write(bytes(json_payload, 'utf8'))

    return byte_stream.getvalue()


def prepare_two_entry_database(a_dataset, another_dataset, client_with_push_user_permissions):
    a_station_id = a_dataset[0]['station_id']
    a_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=a_dataset)
    assert a_dataset_create_result.status_code == HTTPStatus.NO_CONTENT

    another_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=another_dataset)
    assert another_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    client = drop_permissions(client_with_push_user_permissions)

    return a_station_id, client
