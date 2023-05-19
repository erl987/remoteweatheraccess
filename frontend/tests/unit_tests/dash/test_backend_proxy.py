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

import pytest
from dateutil.parser import isoparse

from frontend.django_frontend.weatherpage.dash_weatherpage.backend_proxy import CachedBackendProxy, BackendProxy
# noinspection PyUnresolvedReferences
from tests.unit_tests.mocks import GeneralResponseMock, TempHumiditySensorMock, SensorResponseMock,\
    StationResponseMock, TimeLimitsResponseMock,  get_some_sensor_data, use_dummy_cache_backend, A_SENSOR_ID,\
    SOME_URL, SOME_PORT, SOME_JSON, A_SENSOR_DESCRIPTION, A_UNIT, A_TEMP_HUMIDITY_SENSOR_ID,\
    A_TEMP_SENSOR_DESCRIPTION, A_TEMP_HUMIDITY_SENSOR_DESCRIPTION, A_TEMP_UNIT, A_HUMID_SENSOR_DESCRIPTION,\
    A_HUMID_UNIT, A_STATION_ID, A_FIRST_TIMPOINT, A_LAST_TIMEPOINT


@pytest.mark.usefixtures('requests_mock')
def test_backend_get_all_sensors(requests_mock):
    requests_mock.get('http://something:80/api/v1/station', json=StationResponseMock().json())

    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    stations = backend.get_all_stations()

    assert requests_mock.call_count == 1
    assert stations == StationResponseMock().json()


@pytest.mark.usefixtures('requests_mock')
def test_backend_get_all_available_sensors_without_temperature_or_humidity(requests_mock):
    requests_mock.get('http://something:80/api/v1/sensor', json=SensorResponseMock(False).json())
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    all_available_sensors = backend.get_all_available_sensors()

    assert requests_mock.call_count == 1
    assert all_available_sensors == {A_SENSOR_ID: {'description': A_SENSOR_DESCRIPTION, 'unit': A_UNIT}}


@pytest.mark.usefixtures('requests_mock')
def test_backend_get_all_available_sensors(requests_mock):
    requests_mock.get('http://something:80/api/v1/sensor', json=SensorResponseMock(True).json())
    requests_mock.get('http://something:80/api/v1/temp-humidity-sensor', json=TempHumiditySensorMock().json())
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    all_available_sensors = backend.get_all_available_sensors()

    assert requests_mock.call_count == 2
    assert all_available_sensors == {
        A_SENSOR_ID: {
            'description': A_SENSOR_DESCRIPTION,
            'unit': A_UNIT
        },
        '{}_temp'.format(A_TEMP_HUMIDITY_SENSOR_ID):
            {
                'description': '{} {}'.format(A_TEMP_SENSOR_DESCRIPTION, A_TEMP_HUMIDITY_SENSOR_DESCRIPTION),
                'unit': A_TEMP_UNIT
            },
        '{}_humid'.format(A_TEMP_HUMIDITY_SENSOR_ID):
            {
                'description': '{} {}'.format(A_HUMID_SENSOR_DESCRIPTION, A_TEMP_HUMIDITY_SENSOR_DESCRIPTION),
                'unit': A_HUMID_UNIT
            }
    }


@pytest.mark.usefixtures('requests_mock')
def test_backend_get_available_time_limits(requests_mock):
    requests_mock.get('https://something:80/api/v1/data/limits', json=TimeLimitsResponseMock().json())
    backend = BackendProxy(SOME_URL, SOME_PORT, True)
    available_time_limits = backend.get_available_time_limits()

    assert requests_mock.call_count == 1
    assert available_time_limits == TimeLimitsResponseMock().json()


@pytest.mark.usefixtures('requests_mock')
def test_backend_get_weather_data_in_time_range(requests_mock):
    requests_mock.get('http://something:80/api/v1/data', json=GeneralResponseMock().json())
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    requested_sensors = ['pressure', 'UV', 'IN_temp', 'OUT1_humid']

    time_range = backend.get_weather_data_in_time_range([A_STATION_ID],
                                                        requested_sensors,
                                                        isoparse(A_FIRST_TIMPOINT),
                                                        isoparse(A_LAST_TIMEPOINT))

    assert requests_mock.call_count == 1
    assert time_range == SOME_JSON


@pytest.mark.usefixtures('mocker', 'use_dummy_cache_backend')
def test_cached_backend_time_limits(mocker, use_dummy_cache_backend):
    backend_mock = mocker.patch(
        'frontend.django_frontend.weatherpage.dash_weatherpage.backend_proxy.BackendProxy.get_available_time_limits',
        return_value={
            'first_timepoint': A_FIRST_TIMPOINT,
            'last_timepoint': A_LAST_TIMEPOINT
        })
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False)
    got_first_timepoint, got_last_timepoint = backend.time_limits()

    backend_mock.assert_called_once()
    assert got_first_timepoint == A_FIRST_TIMPOINT
    assert got_last_timepoint == A_LAST_TIMEPOINT


@pytest.mark.usefixtures('mocker', 'use_dummy_cache_backend')
def test_cached_backend_data(mocker, use_dummy_cache_backend):
    backend_mock = mocker.patch(
        'frontend.django_frontend.weatherpage.dash_weatherpage.backend_proxy.BackendProxy.'
        'get_weather_data_in_time_range',
        return_value=get_some_sensor_data())
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False)
    got_data = backend.data([A_STATION_ID], [A_SENSOR_ID], A_FIRST_TIMPOINT, A_LAST_TIMEPOINT)

    backend_mock.assert_called_once()
    assert got_data == get_some_sensor_data()


@pytest.mark.usefixtures('mocker', 'use_dummy_cache_backend')
def test_cached_backend_available_sensors(mocker, use_dummy_cache_backend):
    expected_sensor_data = {
        A_SENSOR_ID: {
            'description': A_SENSOR_DESCRIPTION,
            'unit': A_UNIT
        }
    }
    backend_mock = mocker.patch(
        'frontend.django_frontend.weatherpage.dash_weatherpage.backend_proxy.BackendProxy.get_all_available_sensors',
        return_value=expected_sensor_data)
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False)
    available_sensors, available_sensors_data = backend.available_sensors()

    backend_mock.assert_called_once()
    assert available_sensors_data == expected_sensor_data
    assert available_sensors == [{
        'label': A_SENSOR_DESCRIPTION,
        'value': A_SENSOR_ID
    }]


@pytest.mark.usefixtures('mocker', 'use_dummy_cache_backend')
def test_cached_backend_available_stations(mocker, use_dummy_cache_backend):
    expected_station_data = [{
        'station_id': A_STATION_ID,
        'location': 'Location/DE'
    }]
    backend_mock = mocker.patch(
        'frontend.django_frontend.weatherpage.dash_weatherpage.backend_proxy.BackendProxy.get_all_stations',
        return_value=expected_station_data)

    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False)
    available_stations, available_stations_data, available_station_ids = backend.available_stations()

    backend_mock.assert_called_once()
    assert available_stations == [{
        'label': 'Location',
        'value': A_STATION_ID
    }]
    assert available_stations_data == expected_station_data
    assert available_station_ids == [A_STATION_ID]
