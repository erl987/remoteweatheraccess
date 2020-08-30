from http import HTTPStatus

import pytest

# noinspection PyUnresolvedReferences
from ..utils import client_without_permissions  # required as a fixture


@pytest.mark.usefixtures('client_without_permissions')
def test_get_all_sensors(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor')
    assert result.status_code == HTTPStatus.OK
    returned_json = result.get_json()
    assert len(returned_json) == 10


@pytest.mark.usefixtures('client_without_permissions')
def test_get_one_sensor(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor/pressure')
    assert result.status_code == HTTPStatus.OK
    assert result.get_json()['unit'] == 'Pa'


@pytest.mark.usefixtures('client_without_permissions')
def test_get_one_invalid_sensor(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor/invalid')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST
