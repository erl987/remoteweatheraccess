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
import logging
from datetime import datetime
from http import HTTPStatus
from io import BytesIO
from json import JSONEncoder
from typing import List, Dict

import pytest
from flask_jwt_extended import create_access_token

from backend_app import create_app
from backend_config.settings import TestConfig
from backend_src.extensions import db
from backend_src.models import WeatherStation, create_temp_humidity_sensors, create_sensors
from backend_src.utils import Role


@pytest.fixture
def a_dataset() -> List[Dict]:
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
def an_updated_dataset() -> List[Dict]:
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
def another_dataset() -> List[Dict]:
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
def a_dataset_with_rain_counter_reset() -> List[Dict]:
    yield [
        {
            'timepoint': '2016-02-06T15:30:36.2Z',
            'station_id': 'TES',
            'pressure': 1019.2,
            'uv': 2.4,
            'rain_counter': 970.5,
            'direction': 350.2,
            'speed': 95.2,
            'wind_temperature': 9.8,
            'gusts': 120.5,
            'temperature_humidity': [{
                'sensor_id': 'IN',
                'temperature': 29.5,
                'humidity': 58.0
            }]
        },
        {
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
        },
        {
            'timepoint': '2016-02-06T15:50:36.2Z',
            'station_id': 'TES',
            'pressure': 1018.2,
            'uv': 2.6,
            'rain_counter': 0,
            'direction': 350.2,
            'speed': 95.2,
            'wind_temperature': 9.8,
            'gusts': 120.5,
            'temperature_humidity': [{
                'sensor_id': 'IN',
                'temperature': 21.3,
                'humidity': 52.5
            }]
        },
        {
            'timepoint': '2016-02-06T16:00:36.2Z',
            'station_id': 'TES',
            'pressure': 1018.2,
            'uv': 2.6,
            'rain_counter': 2.5,
            'direction': 350.2,
            'speed': 95.2,
            'wind_temperature': 9.8,
            'gusts': 120.5,
            'temperature_humidity': [{
                'sensor_id': 'IN',
                'temperature': 19.6,
                'humidity': 56.2
            }]
        }
    ]


@pytest.fixture
def another_dataset_without_timezone() -> List[Dict]:
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
def a_dataset_for_another_station() -> List[Dict]:
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
def a_dataset_with_none() -> List[Dict]:
    yield [{
        'timepoint': '2016-02-06T15:40:36.2Z',
        'station_id': 'TES',
        'pressure': None,
        'uv': 9.6,
        'rain_counter': 980.5,
        'direction': 190.5,
        'speed': 95.2,
        'wind_temperature': 9.8,
        'gusts': 120.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 10.5,
            'humidity': None
        }]
    }]


@pytest.fixture
def a_dataset_with_a_duplicate_time_point() -> List[Dict]:
    yield [{
        'timepoint': '2016-02-05T15:40:36.078357',
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
    }, {
        'timepoint': '2016-02-05T15:40:36.078357',
        'station_id': 'TES',
        'pressure': 1030.5,
        'uv': 13.6,
        'rain_counter': 982.5,
        'direction': 210.5,
        'speed': 91.2,
        'wind_temperature': -2.8,
        'gusts': 130.5,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 12.5,
            'humidity': 80.5
        }]
    }, {
        'timepoint': '2016-02-05T16:40:36.078357',
        'station_id': 'TES',
        'pressure': 1040.5,
        'uv': 12.6,
        'rain_counter': 990.5,
        'direction': 220.5,
        'speed': 93.2,
        'wind_temperature': 5.8,
        'gusts': 20.8,
        'temperature_humidity': [{
            'sensor_id': 'IN',
            'temperature': 9.5,
            'humidity': 80.5
        }]
    }]


@pytest.fixture
def a_dataset_with_missing_outside_sensor_data() -> List[Dict]:
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
        'temperature_humidity': [
            {
                'sensor_id': 'IN',
                'temperature': 10.5,
                'humidity': 90.5
            },
            {
                'sensor_id': 'OUT1',
                'temperature': 21.3,
                'humidity': 42.6
            }
        ]
    }, {
        'timepoint': '2016-02-05T15:50:36.078357+01:00',
        'station_id': 'TES',
        'pressure': 1030.5,
        'uv': 13.6,
        'rain_counter': 982.5,
        'direction': 210.5,
        'speed': 91.2,
        'wind_temperature': -2.8,
        'gusts': 130.5,
        'temperature_humidity': [
            {
                'sensor_id': 'IN',
                'temperature': 12.5,
                'humidity': 80.5
            }
        ]
    }, {
        'timepoint': '2016-02-05T16:40:36.078357+01:00',
        'station_id': 'TES',
        'pressure': 1040.5,
        'uv': 12.6,
        'rain_counter': 990.5,
        'direction': 220.5,
        'speed': 93.2,
        'wind_temperature': 5.8,
        'gusts': 20.8,
        'temperature_humidity': [
            {
                'sensor_id': 'IN',
                'temperature': 9.5,
                'humidity': 80.5
            },
            {
                'sensor_id': 'OUT1',
                'temperature': 26.4,
                'humidity': 48.9
            }
        ]
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
        # noinspection PyTypeChecker
        admin_access_token = create_access_token(identity={'name': 'pytest_user', 'role': Role.PUSH_USER.name},
                                                 additional_claims={'station_id': 'TES'},
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
        # noinspection PyTypeChecker
        admin_access_token = create_access_token(identity={'name': 'pytest_admin', 'role': Role.ADMIN.name},
                                                 additional_claims={'station_id': None},
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


class IsoDateTimeJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


def zip_payload(object_payload) -> bytes:
    json_payload = json.dumps(object_payload, cls=IsoDateTimeJSONEncoder)
    byte_stream = BytesIO()
    with gzip.GzipFile(fileobj=byte_stream, mode='w') as g:
        g.write(bytes(json_payload, 'utf8'))

    return byte_stream.getvalue()


def prepare_two_entry_database(first_dataset, second_dataset, client_with_push_user_permissions):
    a_station_id = first_dataset[0]['station_id']
    first_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=first_dataset)
    assert first_dataset_create_result.status_code == HTTPStatus.NO_CONTENT

    second_dataset_create_result = client_with_push_user_permissions.post('/api/v1/data', json=second_dataset)
    assert second_dataset_create_result.status_code == HTTPStatus.NO_CONTENT
    client = drop_permissions(client_with_push_user_permissions)

    return a_station_id, client
