import json
import pytest

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # required as fixture

from frontend.src.utils import Backend

SOME_PORT = 80
SOME_URL = 'http://something'
A_STATION_ID = 'TES'
A_SENSOR_ID = 'pressure'
A_UNIT = 'Pa'
A_TEMP_UNIT = 'degree C'
A_HUMID_UNIT = 'percent'
A_SENSOR_DESCRIPTION = 'a description'
A_TEMP_HUMIDITY_SENSOR_ID = 'IN'
A_TEMP_HUMIDITY_SENSOR_DESCRIPTION = 'innen'
A_TEMP_SENSOR_DESCRIPTION = 'a temperature sensor'
A_HUMID_SENSOR_DESCRIPTION = 'a humid sensor'
SOME_JSON = {'response': 'something'}


class GeneralResponseMock(object):
    def json(self):
        return SOME_JSON


class TempHumiditySensorMock(object):
    def json(self):
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


def _create_requests_mock(mocker, response_mock):
    return mocker.patch('requests.Session.get', return_value=response_mock)


@pytest.mark.usefixtures('mocker')
def test_get_all_sensors(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = Backend(SOME_URL, SOME_PORT)
    stations = backend.get_all_stations()

    http_mock.assert_called_once()
    assert stations == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_get_all_available_sensors_without_temperature_or_humidity(mocker):
    http_mock = _create_requests_mock(mocker, SensorResponseMock(False))
    backend = Backend(SOME_URL, SOME_PORT)
    all_available_sensors = backend.get_all_available_sensors()

    http_mock.assert_called_once()
    assert all_available_sensors == {A_SENSOR_ID: {'description': A_SENSOR_DESCRIPTION, 'unit': A_UNIT}}


@pytest.mark.usefixtures('mocker')
def test_get_all_available_sensors(mocker):
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
def test_get_available_time_limits(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = Backend(SOME_URL, SOME_PORT)
    available_time_limits = backend.get_available_time_limits()

    http_mock.assert_called_once()
    assert available_time_limits == SOME_JSON


@pytest.mark.usefixtures('mocker')
def test_get_weather_data_in_time_range(mocker):
    http_mock = _create_requests_mock(mocker, GeneralResponseMock())
    backend = Backend(SOME_URL, SOME_PORT)
    first_timepoint = '2020-01-01T00:00:00'
    last_timepoint = '2020-05-01T00:00:00'
    requested_sensors = ['pressure', 'UV', 'IN_temp', 'OUT1_humid']

    time_range = backend.get_weather_data_in_time_range(A_STATION_ID, requested_sensors, first_timepoint,
                                                        last_timepoint)

    expected_sensors = ['pressure', 'UV', 'temperature', 'humidity']
    http_mock.assert_called_once()
    assert time_range == SOME_JSON

    sent_data_json = json.loads(http_mock.call_args[1]['data'])
    assert sent_data_json['first_timepoint'] == first_timepoint
    assert sent_data_json['last_timepoint'] == last_timepoint
    assert sent_data_json['stations'] == A_STATION_ID
    assert set(sent_data_json['sensors']) == set(expected_sensors)
