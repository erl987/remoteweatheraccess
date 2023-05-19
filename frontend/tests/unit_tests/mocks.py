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

SOME_PORT = 80
SOME_URL = 'something'

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

A_STATION = {"device": "some",
             "height": 951.0,
             "id": 2,
             "latitude": 89.2345,
             "location": "Some Place",
             "longitude": -25.2345,
             "rain_calib_factor": 0.6820802083333333,
             "station_id": A_STATION_ID}

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


class TimeLimitsResponseMock(object):
    @staticmethod
    def json():
        return {
            'first_timepoint': A_FIRST_TIMPOINT,
            'last_timepoint': A_LAST_TIMEPOINT
        }


class TempHumiditySensorMock(object):
    @staticmethod
    def json():
        return [{
            'sensor_id': A_TEMP_HUMIDITY_SENSOR_ID,
            'description': A_TEMP_HUMIDITY_SENSOR_DESCRIPTION
        }]


class StationResponseMock(object):
    @staticmethod
    def json():
        return [A_STATION]


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


def get_some_sensor_data():
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


@pytest.fixture()
def use_dummy_cache_backend(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
