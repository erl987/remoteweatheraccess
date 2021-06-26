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

from http import HTTPStatus

import pytest

# noinspection PyUnresolvedReferences
from ..utils import client_with_admin_permissions, client_with_push_user_permissions, client_without_permissions, \
    a_station, another_station, an_updated_station  # required as a fixture
from ..utils import drop_permissions


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_create_station(client_with_admin_permissions, a_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED
    returned_json = result.get_json()
    a_stations_with_same_id = dict(a_station)
    a_stations_with_same_id['id'] = 3
    assert returned_json == a_stations_with_same_id

    location_result = client_with_admin_permissions.get(result.headers['Location'])
    assert location_result.status_code == HTTPStatus.OK
    assert location_result.get_json() == returned_json


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station', 'another_station')
def test_create_two_stations(client_with_admin_permissions, a_station, another_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED

    result_2 = client_with_admin_permissions.post('/api/v1/station', json=another_station)
    assert result_2.status_code == HTTPStatus.CREATED

    get_result = client_with_admin_permissions.get('/api/v1/station')
    assert get_result.status_code == HTTPStatus.OK
    assert len(get_result.get_json()) == 4


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_create_same_station_twice(client_with_admin_permissions, a_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED

    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CONFLICT
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_create_station_with_too_long_id(client_with_admin_permissions, a_station):
    invalid_station = dict(a_station)
    invalid_station['station_id'] = ''.join(['a' for _ in range(0, 11)])
    result = client_with_admin_permissions.post('/api/v1/station', json=invalid_station)
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_create_station_with_invalid_body(client_with_admin_permissions, a_station):
    invalid_station = dict(a_station)
    del invalid_station['longitude']
    result = client_with_admin_permissions.post('/api/v1/station', json=invalid_station)
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_create_station_with_wrong_content_type(client_with_admin_permissions):
    result = client_with_admin_permissions.post('/api/v1/station', data={}, content_type='text/html')
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_without_permissions', 'a_station')
def test_create_station_without_required_permissions(client_without_permissions, a_station):
    result = client_without_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.UNAUTHORIZED
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_push_user_permissions', 'a_station')
def test_create_station_with_insufficient_permissions(client_with_push_user_permissions, a_station):
    result = client_with_push_user_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.FORBIDDEN
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_without_permissions')
def test_get_all_stations(client_without_permissions):
    result = client_without_permissions.get('/api/v1/station')
    assert result.status_code == HTTPStatus.OK
    result_json = result.get_json()
    assert len(result_json) == 2


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_get_all_stations_when_database_empty(client_with_admin_permissions):
    result_delete_1 = client_with_admin_permissions.delete('/api/v1/station/1')
    assert result_delete_1.status_code == HTTPStatus.NO_CONTENT
    result_delete_2 = client_with_admin_permissions.delete('/api/v1/station/2')
    assert result_delete_2.status_code == HTTPStatus.NO_CONTENT

    client = drop_permissions(client_with_admin_permissions)
    result = client.get('/api/v1/station')
    assert result.status_code == HTTPStatus.OK
    result_json = result.get_json()
    assert len(result_json) == 0


@pytest.mark.usefixtures('client_without_permissions', 'a_station')
def test_get_one_station(client_without_permissions, a_station):
    result = client_without_permissions.get('/api/v1/station/1')
    assert result.status_code == HTTPStatus.OK
    result_json = result.get_json()
    assert result_json['station_id'] == 'TES'


@pytest.mark.usefixtures('client_without_permissions', 'a_station')
def test_get_one_not_existing_station(client_without_permissions, a_station):
    result = client_without_permissions.get('/api/v1/station/3')
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_without_permissions', 'a_station')
def test_get_one_station_with_invalid_id(client_without_permissions, a_station):
    result = client_without_permissions.get('/api/v1/station/NONE')
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_update_a_station(client_with_admin_permissions, a_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED

    expected_longitude = 40.0
    updated_station = dict(a_station)
    updated_station['longitude'] = expected_longitude
    result = client_with_admin_permissions.put('/api/v1/station/3', json=updated_station)
    assert result.status_code == HTTPStatus.NO_CONTENT

    location_result = client_with_admin_permissions.get(result.headers['Location'])
    assert location_result.status_code == HTTPStatus.OK
    assert location_result.get_json()['longitude'] == expected_longitude


@pytest.mark.usefixtures('client_with_admin_permissions', 'an_updated_station')
def test_update_a_station_when_not_existing(client_with_admin_permissions, an_updated_station):
    result = client_with_admin_permissions.put('/api/v1/station/3', json=an_updated_station)
    assert result.status_code == HTTPStatus.NOT_FOUND
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'an_updated_station')
def test_update_a_station_with_invalid_id(client_with_admin_permissions, an_updated_station):
    result = client_with_admin_permissions.put('/api/v1/station/INVALID', json=an_updated_station)
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'an_updated_station')
def test_update_a_station_with_mismatching_ids(client_with_admin_permissions, an_updated_station):
    invalid_station = dict(an_updated_station)
    invalid_station['station_id'] = 'other'
    result = client_with_admin_permissions.put('/api/v1/station/1', json=an_updated_station)
    assert result.status_code == HTTPStatus.CONFLICT
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station', 'an_updated_station')
def test_update_a_station_with_invalid_body(client_with_admin_permissions, a_station, an_updated_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED

    invalid_station = dict(an_updated_station)
    del invalid_station['longitude']
    result = client_with_admin_permissions.put('/api/v1/station/1', json=invalid_station)
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_update_a_station_with_wrong_content_type(client_with_admin_permissions):
    result = client_with_admin_permissions.put('/api/v1/station/1', data={}, content_type='text/html')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.usefixtures('client_without_permissions', 'an_updated_station')
def test_update_station_without_required_permissions(client_without_permissions, an_updated_station):
    result = client_without_permissions.post('/api/v1/station', json=an_updated_station)
    assert result.status_code == HTTPStatus.UNAUTHORIZED
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_push_user_permissions', 'an_updated_station')
def test_update_station_with_insufficient_permissions(client_with_push_user_permissions, an_updated_station):
    result = client_with_push_user_permissions.post('/api/v1/station', json=an_updated_station)
    assert result.status_code == HTTPStatus.FORBIDDEN
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_admin_permissions', 'a_station')
def test_delete_a_station(client_with_admin_permissions, a_station):
    result = client_with_admin_permissions.post('/api/v1/station', json=a_station)
    assert result.status_code == HTTPStatus.CREATED

    result = client_with_admin_permissions.delete('/api/v1/station/3')
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_delete_a_not_existing_station(client_with_admin_permissions):
    result = client_with_admin_permissions.delete('/api/v1/station/3')
    assert result.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.usefixtures('client_with_admin_permissions')
def test_delete_a_station_with_invalid_id(client_with_admin_permissions):
    result = client_with_admin_permissions.delete('/api/v1/station/NONE')
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_without_permissions')
def test_delete_station_without_required_permissions(client_without_permissions):
    result = client_without_permissions.delete('/api/v1/station/1')
    assert result.status_code == HTTPStatus.UNAUTHORIZED
    assert 'error' in result.get_json()


@pytest.mark.usefixtures('client_with_push_user_permissions')
def test_delete_station_with_insufficient_permissions(client_with_push_user_permissions):
    result = client_with_push_user_permissions.delete('/api/v1/station/1')
    assert result.status_code == HTTPStatus.FORBIDDEN
    assert 'error' in result.get_json()
