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

from hashlib import md5
from http import HTTPStatus
from logging import getLogger
from typing import List

from django.core.cache import cache
from requests import Session
from requests.adapters import Retry

from .utils import Singleton, TimeoutHTTPAdapter, TEMP_SENSOR_MARKER, HUMID_SENSOR_MARKER, DEWPOINT_SENSOR_MARKER, \
    is_dewpoint_sensor
from .utils import get_url_encoded_iso_time_string
from .utils import is_temp_sensor, is_humidity_sensor

logger = getLogger('django')


class CachedBackendProxy(object, metaclass=Singleton):
    def __init__(self, backend_url, backend_port, do_use_https):
        self._backend = BackendProxy(backend_url, backend_port, do_use_https)

    def time_limits(self):
        limits = cache.get_or_set('time-limits', self._backend.get_available_time_limits(),
                                  timeout=5 * 60)  # caching period in seconds
        logger.info('Received the current minimum and maximum time limits of the data from the backend')
        return limits['first_timepoint'], limits['last_timepoint']

    def available_sensors(self):
        available_sensors_data = cache.get_or_set('available-sensors', self._backend.get_all_available_sensors(),
                                                  timeout=5 * 60)  # caching period in seconds
        available_sensors = []
        for curr_sensor_id, cur__sensor_data in available_sensors_data.items():
            available_sensors.append({'label': cur__sensor_data['description'], 'value': curr_sensor_id})

        logger.info('Received data for all available sensors from the backend')
        return available_sensors, available_sensors_data

    def latest_data(self):
        latest_data = cache.get_or_set('latest-data', self._backend.get_latest_data(),
                                       timeout=5 * 60)  # caching period in seconds
        logger.info('Received latest data for all stations from the backend')
        return latest_data

    def available_stations(self):
        available_stations = []
        available_station_ids = []
        available_stations_data = cache.get_or_set('available-stations', self._backend.get_all_stations(),
                                                   timeout=5 * 60)  # caching period in seconds

        station_indices = {}
        for index, station in enumerate(available_stations_data):
            curr_station_id = station['station_id']
            available_station_ids.append(curr_station_id)
            station_indices[curr_station_id] = index
        available_station_ids.sort()

        sorted_available_stations_data = []
        for curr_station_id in available_station_ids:
            sorted_available_stations_data.append(available_stations_data[station_indices[curr_station_id]])
            splitted_location_info = sorted_available_stations_data[-1]['location'].split('/')
            station_town = splitted_location_info[0]
            available_stations.append({'label': station_town, 'value': curr_station_id})

        logger.info('Received data for all available stations from the backend')
        return available_stations, sorted_available_stations_data, available_station_ids

    def data(self, chosen_stations, chosen_sensors, start_time, end_time):
        cache_key = self._get_weather_data_request_cache_key(chosen_stations, chosen_sensors, start_time, end_time)
        data = cache.get_or_set(cache_key, self._backend.get_weather_data_in_time_range(chosen_stations, chosen_sensors,
                                                                                        start_time, end_time),
                                timeout=5 * 60)  # caching period in seconds

        logger.info(
            'Received data for stations {}, sensors {} in time period \'{}\'-\'{}\' from the backend'.format(
                chosen_stations,
                chosen_sensors,
                start_time,
                end_time))

        return data

    @staticmethod
    def _get_weather_data_request_cache_key(chosen_stations, chosen_sensors, start_time, end_time):
        chosen_stations_str = ','.join(sorted(chosen_stations))
        chosen_sensors_str = ','.join(sorted(chosen_sensors))

        cache_key = md5(f'{chosen_stations_str}-{chosen_sensors_str}-{start_time}-{end_time}'.encode()).hexdigest()
        return f'weather-data-{cache_key}'


class BackendProxy(object):
    API_VERSION = '/api/v1'
    DEFAULT_TIMEOUT_IN_SEC = 20

    def __init__(self, url, port, do_use_https):
        self._http = Session()
        retry_strategy = Retry(
            total=5,
            status_forcelist=[
                HTTPStatus.TOO_MANY_REQUESTS,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                HTTPStatus.BAD_GATEWAY,
                HTTPStatus.SERVICE_UNAVAILABLE,
                HTTPStatus.BAD_GATEWAY
            ],
            backoff_factor=2
        )
        adapter = TimeoutHTTPAdapter(timeout=BackendProxy.DEFAULT_TIMEOUT_IN_SEC, max_retries=retry_strategy)
        if do_use_https:
            self._http.mount('https://', adapter)
            self._scheme = 'https'
        else:
            # noinspection HttpUrlsUsage
            self._http.mount('http://', adapter)
            self._scheme = 'http'

        self._http.hooks['response'] = [lambda response, *args, **kwargs: response.raise_for_status()]

        self._url = url
        self._port = port

    def get_all_stations(self):
        return self._simple_get_request('station')

    def get_available_time_limits(self):
        return self._simple_get_request('data/limits')

    def get_latest_data(self):
        return self._simple_get_request('data/latest')

    def get_all_available_sensors(self):
        available_sensors = {}

        temperature_sensor_info = None
        humidity_sensor_info = None
        dewpoint_sensor_info = None

        sensor_infos = self._simple_get_request('sensor')
        for sensor_info in sensor_infos:
            sensor_id = sensor_info['sensor_id']
            if sensor_id == 'temperature':
                temperature_sensor_info = sensor_info
            elif sensor_id == 'humidity':
                humidity_sensor_info = sensor_info
            elif sensor_id == 'dewpoint':
                dewpoint_sensor_info = sensor_info
            else:
                available_sensors[sensor_id] = {
                    'description': sensor_info['description'],
                    'unit': sensor_info['unit']
                }

        if temperature_sensor_info or humidity_sensor_info or dewpoint_sensor_info:
            sensor_infos = self._simple_get_request('temp-humidity-sensor')
            for sensor_info in sensor_infos:
                temp_sensor_id = sensor_info['sensor_id'] + TEMP_SENSOR_MARKER
                humidity_sensor_id = sensor_info['sensor_id'] + HUMID_SENSOR_MARKER
                dewpoint_sensor_id = sensor_info['sensor_id'] + DEWPOINT_SENSOR_MARKER
                if temperature_sensor_info:
                    available_sensors[temp_sensor_id] = {
                        'description': temperature_sensor_info['description'] + ' ' + sensor_info['description'],
                        'unit': temperature_sensor_info['unit']
                    }
                if humidity_sensor_info:
                    available_sensors[humidity_sensor_id] = {
                        'description': humidity_sensor_info['description'] + ' ' + sensor_info['description'],
                        'unit': humidity_sensor_info['unit']
                    }
                if dewpoint_sensor_info:
                    available_sensors[dewpoint_sensor_id] = {
                        'description': dewpoint_sensor_info['description'] + ' ' + sensor_info['description'],
                        'unit': dewpoint_sensor_info['unit']
                    }

        return available_sensors

    def get_weather_data_in_time_range(self, chosen_stations: List[str], chosen_sensors: List[str],
                                       start_time, end_time):
        provided_sensors = []
        for sensor in chosen_sensors:
            if is_temp_sensor(sensor):
                provided_sensors.append('temperature')
            elif is_humidity_sensor(sensor):
                provided_sensors.append('humidity')
            elif is_dewpoint_sensor(sensor):
                provided_sensors.append('dewpoint')
            else:
                provided_sensors.append(sensor)

        r = self._http.get('{}://{}:{}{}/data?first_timepoint={}&last_timepoint={}&stations={}&sensors={}'.format(
            self._scheme,
            self._url,
            self._port,
            BackendProxy.API_VERSION,
            get_url_encoded_iso_time_string(start_time),
            get_url_encoded_iso_time_string(end_time),
            ",".join(chosen_stations),
            ",".join(provided_sensors))
        )
        return r.json()

    def _simple_get_request(self, endpoint):
        r = self._http.get('{}://{}:{}{}/{}'.format(self._scheme,
                                                    self._url,
                                                    self._port,
                                                    BackendProxy.API_VERSION,
                                                    endpoint))
        return r.json()
