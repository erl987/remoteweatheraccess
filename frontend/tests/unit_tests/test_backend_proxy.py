#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
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
from flask import Flask

from frontend.frontend_src.backend_proxy import CachedBackendProxy, BackendProxy
from frontend.frontend_src.cache import cache

SOME_PORT = 80
SOME_URL = 'http://something'

A_STATION_ID = 'TES'
A_SENSOR_ID = 'pressure'
A_UNIT = 'Pa'
A_TEMP_UNIT = 'degree C'
A_HUMID_UNIT = 'percent'
A_SENSOR_DESCRIPTION = 'a description'
A_TEMP_HUMIDITY_SENSOR_ID = 'IN'
A_TEMP_HUMIDITY_SENSOR_DESCRIPTION = 'inside'
A_TEMP_SENSOR_DESCRIPTION = 'a temperature sensor'
A_HUMID_SENSOR_DESCRIPTION = 'a humid sensor'

SOME_JSON = {'response': 'something'}

A_FIRST_TIMPOINT = '2020-01-01T20:00:00'
A_LAST_TIMEPOINT = '2020-01-01T23:15:00'

EXPECTED_SENSOR_DATA = [1013.0, 1015.1, 1014.2]
EXPECTED_TEMP_SENSOR_DATA = [10.5, 9.4, 8.3, 8.6]
EXPECTED_HUMIDITY_SENSOR_DATA = [80.4, 70.5, 59.1, 65.2]


class GeneralResponseMock(object):
    @staticmethod
    def json():
        return SOME_JSON


class TempHumiditySensorMock(object):
    @staticmethod
    def json():
        return [{
            'sensor_id': A_TEMP_HUMIDITY_SENSOR_ID,
            'description': A_TEMP_HUMIDITY_SENSOR_DESCRIPTION
        }]


class SensorResponseMock(object):
    def __init__(self, with_temp_humidity):
        self._with_temp_humidity = with_temp_humidity

    def json(self):
        if self._with_temp_humidity:
            return [
                {
                    'sensor_id': A_SENSOR_ID,
                    'description': A_SENSOR_DESCRIPTION,
                    'unit': A_UNIT
                },
                {
                    'sensor_id': 'temperature',
                    'description': A_TEMP_SENSOR_DESCRIPTION,
                    'unit': A_TEMP_UNIT
                },
                {
                    'sensor_id': 'humidity',
                    'description': A_HUMID_SENSOR_DESCRIPTION,
                    'unit': A_HUMID_UNIT
                }

            ]
        else:
            return [{
                'sensor_id': A_SENSOR_ID,
                'description': A_SENSOR_DESCRIPTION,
                'unit': A_UNIT
            }]


def _get_some_sensor_data():
    sensor_data = {
        A_STATION_ID: {
            A_SENSOR_ID: EXPECTED_SENSOR_DATA,
            'temperature_humidity': {
                A_TEMP_HUMIDITY_SENSOR_ID: {
                    'temperature': EXPECTED_TEMP_SENSOR_DATA,
                    'humidity': EXPECTED_HUMIDITY_SENSOR_DATA
                }
            }
        }
    }
    return sensor_data


def _create_requests_mock(mocker, response_mock):
    return mocker.patch('requests.Session.get', return_value=response_mock)


@pytest.fixture
def app():
    app = Flask(__name__)
    with app.test_request_context():
        cache.init_app(app)
        yield app


@pytest.mark.usefixtures('mocker')
def test_backend_get_all_sensors(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    stations = backend.get_all_stations()

    http_mock.assert_called_once()
    assert stations == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_backend_get_all_available_sensors_without_temperature_or_humidity(mocker):
    http_mock = _create_requests_mock(mocker, SensorResponseMock(False))
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    all_available_sensors = backend.get_all_available_sensors()

    http_mock.assert_called_once()
    assert all_available_sensors == {A_SENSOR_ID: {'description': A_SENSOR_DESCRIPTION, 'unit': A_UNIT}}


@pytest.mark.usefixtures('mocker')
def test_backend_get_all_available_sensors(mocker):
    http_mock = _create_requests_mock(mocker, None)
    http_mock.side_effect = [SensorResponseMock(True), TempHumiditySensorMock()]
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    all_available_sensors = backend.get_all_available_sensors()

    assert http_mock.call_count == 2
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


@pytest.mark.usefixtures('mocker')
def test_backend_get_available_time_limits(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = BackendProxy(SOME_URL, SOME_PORT, True)
    available_time_limits = backend.get_available_time_limits()

    http_mock.assert_called_once()
    assert available_time_limits == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_backend_get_weather_data_in_time_range(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = BackendProxy(SOME_URL, SOME_PORT, False)
    requested_sensors = ['pressure', 'UV', 'IN_temp', 'OUT1_humid']

    time_range = backend.get_weather_data_in_time_range([A_STATION_ID],
                                                        requested_sensors,
                                                        isoparse(A_FIRST_TIMPOINT),
                                                        isoparse(A_LAST_TIMEPOINT))

    http_mock.assert_called_once()
    assert time_range == SOME_JSON


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_time_limits(mocker, app):
    backend_mock = mocker.patch('frontend.frontend_src.backend_proxy.BackendProxy.get_available_time_limits',
                                return_value={
                                    'first_timepoint': A_FIRST_TIMPOINT,
                                    'last_timepoint': A_LAST_TIMEPOINT
                                })
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False, app)
    got_first_timepoint, got_last_timepoint = backend.time_limits()

    backend_mock.assert_called_once()
    assert got_first_timepoint == A_FIRST_TIMPOINT
    assert got_last_timepoint == A_LAST_TIMEPOINT


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_data(mocker, app):
    backend_mock = mocker.patch('frontend.frontend_src.backend_proxy.BackendProxy.get_weather_data_in_time_range',
                                return_value=_get_some_sensor_data())
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False, app)
    got_data = backend.data([A_STATION_ID], [A_SENSOR_ID], A_FIRST_TIMPOINT, A_LAST_TIMEPOINT)

    backend_mock.assert_called_once()
    assert got_data == _get_some_sensor_data()


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_available_sensors(mocker, app):
    expected_sensor_data = {
        A_SENSOR_ID: {
            'description': A_SENSOR_DESCRIPTION,
            'unit': A_UNIT
        }
    }
    backend_mock = mocker.patch('frontend.frontend_src.backend_proxy.BackendProxy.get_all_available_sensors',
                                return_value=expected_sensor_data)
    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False, app)
    available_sensors, available_sensors_data = backend.available_sensors()

    backend_mock.assert_called_once()
    assert available_sensors_data == expected_sensor_data
    assert available_sensors == [{
        'label': A_SENSOR_DESCRIPTION,
        'value': A_SENSOR_ID
    }]


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_available_stations(mocker, app):
    expected_station_data = [{
        'station_id': A_STATION_ID,
        'location': 'Location/DE'
    }]
    backend_mock = mocker.patch('frontend.frontend_src.backend_proxy.BackendProxy.get_all_stations',
                                return_value=expected_station_data)

    backend = CachedBackendProxy(SOME_URL, SOME_PORT, False, app)
    available_stations, available_stations_data, available_station_ids = backend.available_stations()

    backend_mock.assert_called_once()
    assert available_stations == [{
        'label': 'Location',
        'value': A_STATION_ID
    }]
    assert available_stations_data == expected_station_data
    assert available_station_ids == [A_STATION_ID]
