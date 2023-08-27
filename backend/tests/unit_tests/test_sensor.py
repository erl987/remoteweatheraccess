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

from http import HTTPStatus

import pytest

# noinspection PyUnresolvedReferences
from ..utils import client_without_permissions  # required as a fixture


@pytest.mark.usefixtures('client_without_permissions')
def test_get_all_sensors(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor')
    assert result.status_code == HTTPStatus.OK
    returned_json = result.get_json()
    assert len(returned_json) == 11


@pytest.mark.usefixtures('client_without_permissions')
def test_get_one_sensor(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor/pressure')
    assert result.status_code == HTTPStatus.OK
    assert result.get_json()['unit'] == 'hPa'


@pytest.mark.usefixtures('client_without_permissions')
def test_get_one_invalid_sensor(client_without_permissions):
    result = client_without_permissions.get('/api/v1/sensor/invalid')
    assert 'error' in result.get_json()
    assert result.status_code == HTTPStatus.BAD_REQUEST
