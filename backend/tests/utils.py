import logging

import pytest
from flask_jwt_extended import create_access_token

from backend_app import create_app
from config.settings import TestConfig
from src.extensions import db
from src.models import WeatherStation, create_temp_humidity_sensors, create_sensors
from src.utils import Role


@pytest.fixture
def a_dataset() -> dict:
    yield [{
        'timepoint': '2016-02-05T15:40:36.078357+00:00',
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
        'timepoint': '2016-02-05T15:40:36.078357+00:00',
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
def a_user() -> dict:
    yield dict(
        name='test_user',
        password='d5df93*!B',
        role='PUSH_USER',
        station_id='TES')


@pytest.fixture
def an_updated_user() -> dict:
    yield dict(
        name='test_user',
        password='updated_pw',
        role='ADMIN',
        station_id='TES')


@pytest.fixture
def another_user() -> dict:
    yield dict(
        name='test_user_2',
        password='bdfdfd53*!B',
        role='PULL_USER',
        station_id='TES')


@pytest.fixture
def client_without_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    yield client


@pytest.fixture
def client_with_admin_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_station()
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


@pytest.fixture
def client_with_push_user_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger('wsgi').parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_station()
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
        _create_mock_weather_station()
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


def _create_mock_weather_station():
    test_weather_station = WeatherStation()
    test_weather_station.station_id = 'TES'
    test_weather_station.device = 'DEVICE'
    test_weather_station.latitude = -25.05
    test_weather_station.longitude = -2.5
    test_weather_station.location = 'The Location'
    test_weather_station.height = -2.5
    test_weather_station.rain_calib_factor = 0.9
    db.create_all()
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
