import json
import math
import os
from datetime import datetime, timedelta
from http import HTTPStatus
from json.encoder import JSONEncoder
from pathlib import Path

import dateutil.parser
import requests
from requests.adapters import HTTPAdapter, Retry

from frontend.src.cache import cache

HUMID_SENSOR_MARKER = '_humid'
TEMP_SENSOR_MARKER = '_temp'


def _is_temp_sensor(sensor_id):
    return sensor_id.endswith(TEMP_SENSOR_MARKER)


def _is_humidity_sensor(sensor_id):
    return sensor_id.endswith(HUMID_SENSOR_MARKER)


def _get_temp_humidity_sensor_id(sensor_id):
    return sensor_id.split('_')[0]


def get_sensor_data(data, station_id, sensor_id):
    if _is_temp_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['temperature']
    elif _is_humidity_sensor(sensor_id):
        sensor_data = data[station_id]['temperature_humidity'][_get_temp_humidity_sensor_id(sensor_id)]['humidity']
    else:
        sensor_data = data[station_id][sensor_id]
    return sensor_data


def floor_to_n(val, n):
    return math.floor(val / n) * n


def ceil_to_n(val, n):
    return math.ceil(val / n) * n


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CachedBackend(object, metaclass=Singleton):
    def __init__(self, backend_url, backend_port, app):
        self._backend = Backend(backend_url, backend_port)
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


class Backend(object):
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
        adapter = TimeoutHTTPAdapter(timeout=Backend.DEFAULT_TIMEOUT_IN_SEC, max_retries=retry_strategy)
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
            if _is_temp_sensor(sensor):
                provided_sensors.append('temperature')
            elif _is_humidity_sensor(sensor):
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

        r = self._http.get('http://{}:{}{}/data'.format(self._url, self._port, Backend.API_VERSION),
                           data=json.dumps(request_payload, cls=IsoDatetimeJSONEncoder),
                           headers=headers)
        return r.json()

    def _simple_get_request(self, endpoint):
        r = self._http.get('http://{}:{}{}/{}'.format(self._url, self._port, Backend.API_VERSION, endpoint))
        return r.json()


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            raise SyntaxError('Timeout parameter is missing')
        self._timeout = kwargs['timeout']
        del kwargs['timeout']
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = self._timeout
        return super().send(request, **kwargs)


class IsoDatetimeJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


def determine_start_and_end_dates(start_time_str, end_time_str):
    if start_time_str is not None:
        actual_start_time = dateutil.parser.parse(start_time_str)
        start_date = datetime(actual_start_time.year, actual_start_time.month, actual_start_time.day)
    else:
        start_date = None

    if end_time_str is not None:
        actual_end_time = dateutil.parser.parse(end_time_str)
        end_date = datetime(actual_end_time.year, actual_end_time.month, actual_end_time.day) + timedelta(days=1)
    else:
        end_date = None

    return start_date, end_date


def update_bounded_index(index, index_list):
    index += 1
    if index >= len(index_list):
        index = 0
    return index


def convert_input_into_lists(chosen_sensors, chosen_stations):
    if isinstance(chosen_stations, str):
        chosen_stations = [chosen_stations]

    if isinstance(chosen_sensors, str):
        chosen_sensors = [chosen_sensors]

    return chosen_sensors, chosen_stations


def get_current_date(time_zone):
    return datetime.now(time_zone).date()
