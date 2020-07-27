import logging
import pytest
from flask_jwt_extended import create_access_token

from src.extensions import db
from src.models import WeatherStation
from ..config.settings import TestConfig
from ..application import create_app
from ..src.utils import Role


@pytest.fixture
def a_dataset() -> dict:
    yield dict(
        timepoint='2016-02-05T15:40:36.078357+00:00',
        temp=-19.5,
        humidity=10)


@pytest.fixture
def an_updated_dataset() -> dict:
    yield dict(
        timepoint='2016-02-05T15:40:36.078357+00:00',
        temp=12.5,
        humidity=24)


@pytest.fixture
def another_dataset() -> dict:
    yield dict(
        timepoint='2016-02-06T15:40:36.2Z',
        temp=23.5,
        humidity=53)


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
        station_id=None)


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
    logging.getLogger("wsgi").parent.handlers = []

    yield client


@pytest.fixture
def client_with_admin_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger("wsgi").parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_station()
        admin_access_token = create_access_token(identity={'name': 'pytest_admin'},
                                                 user_claims={'role': Role.ADMIN.name, 'station_id': None},
                                                 expires_delta=False,
                                                 fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    yield client


@pytest.fixture
def client_with_push_user_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger("wsgi").parent.handlers = []

    with app.test_request_context():
        _create_mock_weather_station()
        admin_access_token = create_access_token(identity={'name': 'pytest_user'},
                                                 user_claims={'role': Role.PUSH_USER.name, 'station_id': 'TES'},
                                                 expires_delta=False,
                                                 fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    yield client


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


def drop_permissions(client):
    del client.environ_base['HTTP_AUTHORIZATION']
    return client


def drop_registration_details_for_user(user):
    del user["station_id"]
    del user["role"]
