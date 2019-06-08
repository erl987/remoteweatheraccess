import logging
import pytest
from flask_jwt_extended import create_access_token

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
        admin_access_token = create_access_token(identity={'name': 'pytest_admin', 'role': Role.ADMIN.name},
                                                 expires_delta=False, fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    yield client


@pytest.fixture
def client_with_user_permissions():
    app = create_app(TestConfig())
    client = app.test_client()
    logging.getLogger("wsgi").parent.handlers = []

    with app.test_request_context():
        admin_access_token = create_access_token(identity={'name': 'pytest_user', 'role': Role.USER.name},
                                                 expires_delta=False, fresh=True)
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer {}'.format(admin_access_token)

    yield client


def drop_permissions(client):
    del client.environ_base['HTTP_AUTHORIZATION']
    return client
