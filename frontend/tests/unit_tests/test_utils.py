import json
from datetime import datetime

import pytest
from flask import Flask

from frontend.src.utils import Backend, CachedBackend, floor_to_n, ceil_to_n, get_sensor_data
from frontend.src.utils import determine_start_and_end_dates
from frontend.src.cache import cache

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
    backend = Backend(SOME_URL, SOME_PORT)
    stations = backend.get_all_stations()

    http_mock.assert_called_once()
    assert stations == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_backend_get_all_available_sensors_without_temperature_or_humidity(mocker):
    http_mock = _create_requests_mock(mocker, SensorResponseMock(False))
    backend = Backend(SOME_URL, SOME_PORT)
    all_available_sensors = backend.get_all_available_sensors()

    http_mock.assert_called_once()
    assert all_available_sensors == {A_SENSOR_ID: {'description': A_SENSOR_DESCRIPTION, 'unit': A_UNIT}}


@pytest.mark.usefixtures('mocker')
def test_backend_get_all_available_sensors(mocker):
    http_mock = _create_requests_mock(mocker, None)
    http_mock.side_effect = [SensorResponseMock(True), TempHumiditySensorMock()]
    backend = Backend(SOME_URL, SOME_PORT)
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
    backend = Backend(SOME_URL, SOME_PORT)
    available_time_limits = backend.get_available_time_limits()

    http_mock.assert_called_once()
    assert available_time_limits == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_backend_get_weather_data_in_time_range(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = Backend(SOME_URL, SOME_PORT)
    requested_sensors = ['pressure', 'UV', 'IN_temp', 'OUT1_humid']

    time_range = backend.get_weather_data_in_time_range(A_STATION_ID, requested_sensors,
                                                        A_FIRST_TIMPOINT, A_LAST_TIMEPOINT)

    expected_sensors = ['pressure', 'UV', 'temperature', 'humidity']
    http_mock.assert_called_once()
    assert time_range == SOME_JSON

    sent_data_json = json.loads(http_mock.call_args[1]['data'])
    assert sent_data_json['first_timepoint'] == A_FIRST_TIMPOINT
    assert sent_data_json['last_timepoint'] == A_LAST_TIMEPOINT
    assert sent_data_json['stations'] == A_STATION_ID
    assert set(sent_data_json['sensors']) == set(expected_sensors)


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_time_limits(mocker, app):
    backend_mock = mocker.patch('frontend.src.utils.Backend.get_available_time_limits',
                                return_value={
                                    'first_timepoint': A_FIRST_TIMPOINT,
                                    'last_timepoint': A_LAST_TIMEPOINT
                                })
    backend = CachedBackend(SOME_URL, SOME_PORT, app)
    got_first_timepoint, got_last_timepoint = backend.time_limits()

    backend_mock.assert_called_once()
    assert got_first_timepoint == A_FIRST_TIMPOINT
    assert got_last_timepoint == A_LAST_TIMEPOINT


@pytest.mark.usefixtures('mocker', 'app')
def test_cached_backend_data(mocker, app):
    backend_mock = mocker.patch('frontend.src.utils.Backend.get_weather_data_in_time_range',
                                return_value=_get_some_sensor_data())
    backend = CachedBackend(SOME_URL, SOME_PORT, app)
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
    backend_mock = mocker.patch('frontend.src.utils.Backend.get_all_available_sensors',
                                return_value=expected_sensor_data)
    backend = CachedBackend(SOME_URL, SOME_PORT, app)
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
    backend_mock = mocker.patch('frontend.src.utils.Backend.get_all_stations',
                                return_value=expected_station_data)

    backend = CachedBackend(SOME_URL, SOME_PORT, app)
    available_stations, available_stations_data, available_station_ids = backend.available_stations()

    backend_mock.assert_called_once()
    assert available_stations == [{
        'label': 'Location',
        'value': A_STATION_ID
    }]
    assert available_stations_data == expected_station_data
    assert available_station_ids == [A_STATION_ID]


def test_floor_to_n():
    floored_val = floor_to_n(14.2, 5)
    assert floored_val == 10


def test_floor_to_n_for_negative_number():
    floored_val = floor_to_n(-14.2, 5)
    assert floored_val == -15


def test_ceil_to_n():
    ceiled_val = ceil_to_n(14.2, 5)
    assert ceiled_val == 15


def test_ceil_to_n_for_negative_number():
    ceiled_val = ceil_to_n(-14.2, 5)
    assert ceiled_val == -10


def test_get_sensor_data():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, A_SENSOR_ID)
    assert got_sensor_data == EXPECTED_SENSOR_DATA


def test_get_sensor_data_for_temperature():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, '{}_temp'.format(A_TEMP_HUMIDITY_SENSOR_ID))
    assert got_sensor_data == EXPECTED_TEMP_SENSOR_DATA


def test_get_sensor_data_for_humidity():
    sensor_data = _get_some_sensor_data()
    got_sensor_data = get_sensor_data(sensor_data, A_STATION_ID, '{}_humid'.format(A_TEMP_HUMIDITY_SENSOR_ID))
    assert got_sensor_data == EXPECTED_HUMIDITY_SENSOR_DATA


def test_get_start_and_end_times():
    start_date, end_date = determine_start_and_end_dates(A_FIRST_TIMPOINT, A_LAST_TIMEPOINT)
    assert start_date == datetime(year=2020, month=1, day=1)
    assert end_date == datetime(year=2020, month=1, day=2)


def test_get_start_and_end_times_when_none():
    start_date, end_date = determine_start_and_end_dates(None, None)
    assert start_date is None
    assert end_date is None
