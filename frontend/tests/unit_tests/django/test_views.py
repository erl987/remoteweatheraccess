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
from unittest.mock import patch

import pytest

# noinspection PyUnresolvedReferences
from ..mocks import use_dummy_cache_backend, TimeLimitsResponseMock, SensorResponseMock, TempHumiditySensorMock, \
    StationResponseMock


@pytest.mark.usefixtures('client', 'db', 'requests_mock', 'use_dummy_cache_backend')
@patch('google.cloud.storage.Client')
def test_main_page(_, client, db, requests_mock, use_dummy_cache_backend):
    requests_mock.get('https://something:443/api/v1/data/limits', json=TimeLimitsResponseMock().json())
    requests_mock.get('https://something:443/api/v1/sensor', json=SensorResponseMock(with_temp_humidity=True).json())
    requests_mock.get('https://something:443/api/v1/temp-humidity-sensor', json=TempHumiditySensorMock().json())
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock().json())

    response = client.get('')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert '<title>Wetterdaten</title>' in response.content.decode()
    assert requests_mock.call_count == 5


def test_policy_page(client, db):
    response = client.get('/policy/')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert '<h1>Datenschutz</h1>' in response.content.decode()


def test_impress_page(client, db):
    response = client.get('/impress/')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert '<h1>Impressum</h1>' in response.content.decode()


@patch('google.cloud.storage.Client')
def test_download_page(_, client, db, requests_mock):
    requests_mock.get('https://something:443/api/v1/station', json=StationResponseMock.json())

    response = client.get('/download/')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
    assert '<title>Download</title>' in response.content.decode()
