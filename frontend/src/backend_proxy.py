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

import json
import os
from http import HTTPStatus
from pathlib import Path

import gevent.monkey
gevent.monkey.patch_all()

import requests
from requests.adapters import Retry

from frontend.src.cache import cache
from frontend.src.utils import Singleton, TimeoutHTTPAdapter, TEMP_SENSOR_MARKER, HUMID_SENSOR_MARKER
from frontend.src.utils import is_temp_sensor, is_humidity_sensor, IsoDatetimeJSONEncoder


class CachedBackendProxy(object, metaclass=Singleton):
    def __init__(self, backend_url, backend_port, app):
        self._backend = BackendProxy(backend_url, backend_port)
        self._app = app

    @cache.memoize(timeout=5 * 60)  # caching period in seconds
    def time_limits(self):
        limits = self._backend.get_available_time_limits()
        self._app.logger.info('Received the current minimum and maximum time limits of the data from the backend')
        return limits['first_timepoint'], limits['last_timepoint']

    @cache.memoize(timeout=5 * 60)  # caching period in seconds
    def available_sensors(self):
        available_sensors_data = self._backend.get_all_available_sensors()
        available_sensors = []
        for curr_sensor_id, cur__sensor_data in available_sensors_data.items():
            available_sensors.append({'label': cur__sensor_data['description'], 'value': curr_sensor_id})

        self._app.logger.info('Received data for all available sensors from the backend')
        return available_sensors, available_sensors_data

    @cache.memoize(timeout=5 * 60)  # caching period in seconds
    def available_stations(self):
        available_stations = []
        available_station_ids = []
        available_stations_data = self._backend.get_all_stations()
        for station in available_stations_data:
            curr_station_id = station['station_id']
            splitted_location_info = station['location'].split('/')
            station_town = splitted_location_info[0]
            available_stations.append({'label': station_town, 'value': curr_station_id})
            available_station_ids.append(curr_station_id)

        self._app.logger.info('Received data for all available stations from the backend')
        return available_stations, available_stations_data, available_station_ids

    @cache.memoize(timeout=5 * 60)  # caching period in seconds
    def data(self, chosen_stations, chosen_sensors, start_time, end_time):
        data = self._backend.get_weather_data_in_time_range(chosen_stations, chosen_sensors, start_time, end_time)

        self._app.logger.info(
            'Received data for stations {}, sensors {} in time period \'{}\'-\'{}\' from the backend'.format(
                chosen_stations,
                chosen_sensors,
                start_time,
                end_time))

        return data

    @cache.memoize(timeout=48 * 3600)  # caching period in seconds
    def get_text_file_content(self, file_path_relative_to_project_root):
        project_root_path = os.path.abspath(Path(os.path.dirname(__file__)).parent)
        absolute_file_path = project_root_path + os.path.sep + file_path_relative_to_project_root

        self._app.logger.info('Read text file \'{}\' from disk'.format(file_path_relative_to_project_root))
        with open(absolute_file_path, 'r', encoding='utf8') as data_protection_policy_file:
            return data_protection_policy_file.read()


class BackendProxy(object):
    API_VERSION = '/api/v1'
    DEFAULT_TIMEOUT_IN_SEC = 20

    def __init__(self, url, port):
        self._http = requests.Session()
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
        self._http.mount('https://', adapter)
        self._http.mount('http://', adapter)

        self._http.hooks['response'] = [lambda response, *args, **kwargs: response.raise_for_status()]

        self._url = url
        self._port = port

    def get_all_stations(self):
        return self._simple_get_request('station')

    def get_available_time_limits(self):
        return self._simple_get_request('data/limits')

    def get_all_available_sensors(self):
        available_sensors = {}

        temperature_sensor_info = None
        humidity_sensor_info = None

        sensor_infos = self._simple_get_request('sensor')
        for sensor_info in sensor_infos:
            sensor_id = sensor_info['sensor_id']
            if sensor_id == 'temperature':
                temperature_sensor_info = sensor_info
            elif sensor_id == 'humidity':
                humidity_sensor_info = sensor_info
            else:
                available_sensors[sensor_id] = {
                    'description': sensor_info['description'],
                    'unit': sensor_info['unit']
                }

        if temperature_sensor_info and humidity_sensor_info:
            sensor_infos = self._simple_get_request('temp-humidity-sensor')
            for sensor_info in sensor_infos:
                temp_sensor_id = sensor_info['sensor_id'] + TEMP_SENSOR_MARKER
                humidity_sensor_id = sensor_info['sensor_id'] + HUMID_SENSOR_MARKER
                available_sensors[temp_sensor_id] = {
                    'description': temperature_sensor_info['description'] + ' ' + sensor_info['description'],
                    'unit': temperature_sensor_info['unit']
                }
                available_sensors[humidity_sensor_id] = {
                    'description': humidity_sensor_info['description'] + ' ' + sensor_info['description'],
                    'unit': humidity_sensor_info['unit']
                }

        return available_sensors

    def get_weather_data_in_time_range(self, chosen_stations, chosen_sensors, start_time, end_time):
        provided_sensors = []
        for sensor in chosen_sensors:
            if is_temp_sensor(sensor):
                provided_sensors.append('temperature')
            elif is_humidity_sensor(sensor):
                provided_sensors.append('humidity')
            else:
                provided_sensors.append(sensor)

        request_payload = {
            'first_timepoint': start_time,
            'last_timepoint': end_time,
            'sensors': provided_sensors,
            'stations': chosen_stations
        }

        headers = {
            'Content-Type': 'application/json'
        }

        r = self._http.get('http://{}:{}{}/data'.format(self._url, self._port, BackendProxy.API_VERSION),
                           data=json.dumps(request_payload, cls=IsoDatetimeJSONEncoder),
                           headers=headers)
        return r.json()

    def _simple_get_request(self, endpoint):
        r = self._http.get('http://{}:{}{}/{}'.format(self._url, self._port, BackendProxy.API_VERSION, endpoint))
        return r.json()
