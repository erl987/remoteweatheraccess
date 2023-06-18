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
import json
import logging
import os
import threading
from datetime import datetime, timedelta
from json import JSONDecodeError
from pathlib import Path
from shutil import copyfile
from subprocess import Popen, PIPE, TimeoutExpired

import pytz

from .rest_client import ServerProxy
from .utils import IsoDateTimeJSONEncoder, IsoDateTimeJSONDecoder

# indices of the data from the station TE923 (invalid data is marked as 'i'), http://te923.fukz.org/documentation.html
TIME = 0  # time [C-time, seconds since epoch]
INSIDE_TEMP = 1  # inside temperature [deg C]
INSIDE_HUMID = 2  # inside humidity [%]
OUTSIDE_TEMP_1 = 3  # outside temperature 1 [deg C]
OUTSIDE_HUMID_1 = 4  # outside humidity 1 [%]
OUTSIDE_TEMP_2 = 5  # outside temperature 2 [deg C]
OUTSIDE_HUMID_2 = 6  # outside humidity 2 [%]
OUTSIDE_TEMP_3 = 7  # outside temperature 3 [deg C]
OUTSIDE_HUMID_3 = 8  # outside humidity 3 [%]
OUTSIDE_TEMP_4 = 9  # outside temperature 4 [deg C]
OUTSIDE_HUMID_4 = 10  # outside humidity 4 [%]
OUTSIDE_TEMP_5 = 11  # outside temperature 5 [deg C]
OUTSIDE_HUMID_5 = 12  # outside humidity 5 [%]
PRESSURE = 13  # air pressure [hPa]
UV = 14  # UV-index [-]
FORECAST = 15  # weather forecast
# [0 - heavy snow
# 1 - little snow
# 2 - heavy rain
# 3 - little rain
# 4 - cloudy
# 5 - some clouds
# 6 - sunny]
STORM_WARNING = 16  # storm warning [ 0 - no warning, 1 - warning]
WIND_DIRECTION = 17  # wind direction [n x 22.5 deg, 0 -> north]
AVERAGE_WIND_SPEED = 18  # average wind speed [m/s]
WIND_GUSTS = 19  # wind gusts[m/s]
TEMP_OF_WIND_SENSOR = 20  # temperature of wind sensor [deg C]
RAIN_COUNTER = 21  # rain counter [tipping bucket counts since last resetting]


class LastKnownStationData(object):
    DATA_FILE = r'last_known_station_data.json'
    BACKUP_FILE = DATA_FILE + '.backup'
    _lock = threading.Lock()
    _instance = None  # type: LastKnownStationData

    def __init__(self, data_dir_path):
        if LastKnownStationData._instance is not None:
            raise AssertionError('This class is a singleton')
        else:
            LastKnownStationData._instance = self

        Path(data_dir_path).mkdir(parents=True, exist_ok=True)
        self._data_file_path = os.path.join(data_dir_path, self.DATA_FILE)
        self._backup_file_path = os.path.join(data_dir_path, self.BACKUP_FILE)
        self._last_read_utc_time_point = datetime.min.replace(tzinfo=pytz.UTC)
        self._read_from_disk()

    @staticmethod
    def get(data_dir_path):
        with LastKnownStationData._lock:
            if LastKnownStationData._instance is None:
                LastKnownStationData(data_dir_path)

            return LastKnownStationData._instance

    def get_utc_time_point(self):
        return self._last_read_utc_time_point

    def set_utc_time_point(self, last_local_time_point):
        self._last_read_utc_time_point = last_local_time_point.astimezone(pytz.UTC)
        self._write_to_disk()

    def _write_to_disk(self):
        # if the file will get corrupt later, the copy is guaranteed to be valid
        try:
            copyfile(self._data_file_path, self._backup_file_path)
        except FileNotFoundError:
            pass

        with open(self._data_file_path, 'w') as file:
            json.dump({
                'last_utc_time_point': self._last_read_utc_time_point
            }, file, cls=IsoDateTimeJSONEncoder)

    def _read_from_disk(self):
        try:
            self._perform_read_from_disk(self._data_file_path, do_fail_on_not_existing=False)
        except (JSONDecodeError, KeyError):
            # the file was corrupt
            self._perform_read_from_disk(self._backup_file_path, do_fail_on_not_existing=True)

            # correct the file and backup
            self._write_to_disk()
            os.remove(self._backup_file_path)

    def _perform_read_from_disk(self, file_path, do_fail_on_not_existing):
        try:
            with open(file_path, 'r') as file:
                read_data = json.load(file, cls=IsoDateTimeJSONDecoder)
                self._last_read_utc_time_point = read_data['last_utc_time_point'].astimezone(pytz.UTC)
        except FileNotFoundError:
            if do_fail_on_not_existing:
                raise
            else:
                self._last_read_utc_time_point = datetime.min.replace(tzinfo=pytz.UTC)


class WeatherStationProxy(object):
    def __init__(self, config, data_dir_path, weather_data_reader_path):
        self._server_proxy = ServerProxy(config)
        self.data_dir_path = data_dir_path
        self._weather_data_reader_path = weather_data_reader_path
        self._local_time_zone = pytz.timezone(os.getenv('TZ', 'UTC'))

        self._station_id = config['station_id']
        self._read_period_in_minutes = config['data_reading']['read_period_in_minutes']
        self._ignored_data_fields = config['ignored_data_fields']
        self._all_datasets_read_timeout_in_min = config['timeouts_in_min']['all_datasets_read']
        self._latest_dataset_read_timeout_in_min = config['timeouts_in_min']['latest_dataset_read']

        logging.info('Timezone of read data: {}'.format(self._local_time_zone))
        self._log_data_reader_version()

    def _log_data_reader_version(self):
        version_info_str = self._call_data_reader_in_subprocess(self._latest_dataset_read_timeout_in_min, '-v')
        logging.info('Using this weather station data reader: {}'.format(version_info_str.strip()))

    def read_and_send_with_automatic_choice(self):
        last_read_utc_time_point = LastKnownStationData.get(self.data_dir_path).get_utc_time_point()
        time_difference = datetime.utcnow().replace(tzinfo=pytz.UTC) - last_read_utc_time_point
        if time_difference < 2 * timedelta(minutes=self._read_period_in_minutes):
            do_read_all_datasets = False
        else:
            do_read_all_datasets = True

        self.read_and_send(do_read_all_datasets)
        if do_read_all_datasets:
            return True
        else:
            return False

    def read_and_send(self, do_read_all_datasets):
        json_data = self._perform_read_data(do_read_all_datasets)
        self._server_proxy.send_data(json_data, self._station_id)

        # the data is guaranteed to be persisted on the server now
        if len(json_data) > 0:
            LastKnownStationData.get(self.data_dir_path).set_utc_time_point(json_data[-1]['timepoint'])
            logging.info('Read data for time period {} - {} ({} timepoint(s)) and sent it successfully to the '
                         'backend ({}:{})'.format(json_data[0]['timepoint'],
                                                  json_data[-1]['timepoint'],
                                                  len(json_data),
                                                  self._server_proxy.url,
                                                  self._server_proxy.port))
        else:
            logging.info('All read data had already been sent to the backend')

        return len(json_data) > 0

    def _perform_read_data(self, do_read_all_datasets):
        if do_read_all_datasets:
            logging.debug('Reading all available data from the weather station (this takes several minutes)')
            raw_data_str = self._call_data_reader_in_subprocess(self._all_datasets_read_timeout_in_min, '-b')
        else:
            logging.debug('Reading the latest dataset from the weather station')
            raw_data_str = self._call_data_reader_in_subprocess(self._latest_dataset_read_timeout_in_min)

        data = self._parse_raw_data(raw_data_str)
        data = self._to_float_or_none(data)

        json_data = self._to_json(data)
        json_data = self._replace_potentially_wrong_time_stamp(json_data, do_read_all_datasets)
        json_data = self._remove_time_points_from_the_future(json_data)
        json_data = self._filter_out_already_read_time_points(json_data, do_read_all_datasets)

        return json_data

    def _call_data_reader_in_subprocess(self, timeout_in_min: int, flag: str = None):
        command = [self._weather_data_reader_path]
        if flag:
            command.append(flag)

        data_reader_process = Popen(command,
                                    stdout=PIPE,
                                    stderr=PIPE,
                                    text=True)
        try:
            stdout_str, stderr_str = data_reader_process.communicate(timeout=60 * timeout_in_min)
        except TimeoutExpired:
            data_reader_process.kill()
            _, _ = data_reader_process.communicate()
            raise ConnectionError('Connection to the weather station has timed out after {} minute(s)'
                                  .format(timeout_in_min))

        if len(stderr_str) > 0 or data_reader_process.returncode != 0:
            raise ConnectionError('No connection to the weather station was possible (return code: {}, error: {})'
                                  .format(data_reader_process.returncode, stderr_str.strip()))

        return stdout_str

    def _to_json(self, data):
        json_data = []

        for dataset in data:
            local_time = datetime.fromtimestamp(int(dataset[TIME]), self._local_time_zone)

            dataset_json = self._create_dataset(dataset, local_time)

            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'OUT1',
                                                                                 OUTSIDE_TEMP_1, OUTSIDE_HUMID_1))
            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'OUT2',
                                                                                 OUTSIDE_TEMP_2, OUTSIDE_HUMID_2))
            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'OUT3',
                                                                                 OUTSIDE_TEMP_3, OUTSIDE_HUMID_3))
            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'OUT4',
                                                                                 OUTSIDE_TEMP_4, OUTSIDE_HUMID_4))
            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'OUT5',
                                                                                 OUTSIDE_TEMP_5, OUTSIDE_HUMID_5))
            dataset_json['temperature_humidity'].append(self._to_temp_humid_json(dataset, 'IN',
                                                                                 INSIDE_TEMP, INSIDE_HUMID))
            dataset_json['temperature_humidity'] = [x for x in dataset_json['temperature_humidity'] if len(x) > 0]

            dataset_json = self._remove_ignored_data_fields(dataset_json)
            json_data.append(dataset_json)

        return json_data

    def _create_dataset(self, dataset, local_time):
        return {
            'timepoint': local_time,
            'station_id': self._station_id,
            'pressure': dataset[PRESSURE],
            'uv': dataset[UV],
            'rain_counter': int(dataset[RAIN_COUNTER]),
            'speed': dataset[AVERAGE_WIND_SPEED],
            'gusts': dataset[WIND_GUSTS],
            'direction': dataset[WIND_DIRECTION],
            'wind_temperature': dataset[TEMP_OF_WIND_SENSOR],
            'forecast': int(dataset[FORECAST]),
            'storm_warning': int(dataset[STORM_WARNING]),
            'temperature_humidity': []
        }

    @staticmethod
    def _to_temp_humid_json(dataset, sensor_id, temp_index, humid_index):
        temperature = dataset[temp_index]
        humidity = dataset[humid_index]
        if temperature is None and humidity is None:
            return {}
        else:
            return {
                'sensor_id': sensor_id,
                'temperature': temperature,
                'humidity': humidity
            }

    @staticmethod
    def _to_float_or_none(data):
        # invalid data is marked by 'i'
        for index, dataset in enumerate(data):
            data[index] = [None if entry == 'i' else float(entry) for entry in dataset]
        return data

    def _replace_potentially_wrong_time_stamp(self, json_data, do_read_all_datasets):
        if not do_read_all_datasets:
            # the time-stamp provided by "last time point" requests from the station can be wrong
            # all time-stamps of the data do have generally second-resolution
            json_data[0]['timepoint'] = datetime.now(tz=self._local_time_zone).replace(microsecond=0)
        return json_data

    def _remove_time_points_from_the_future(self, json_data):
        # the station may provide time points lying in the future
        curr_time = datetime.now(tz=self._local_time_zone)
        json_data = [entry for entry in json_data if
                     entry['timepoint'] < (curr_time + timedelta(minutes=self._read_period_in_minutes))]
        return json_data

    def _filter_out_already_read_time_points(self, json_data, do_read_all_datasets):
        # the station returns all data available in the memory, but a part of that had already been read earlier
        if do_read_all_datasets:
            last_read_utc_time_point = LastKnownStationData.get(self.data_dir_path).get_utc_time_point()
            local_last_read_dataset_time = last_read_utc_time_point.replace(tzinfo=pytz.utc)
            local_last_read_dataset_time.astimezone(self._local_time_zone)
            json_data = [entry for entry in json_data if entry['timepoint'] > local_last_read_dataset_time]
        return json_data

    @staticmethod
    def _parse_raw_data(raw_data_str):
        raw_data = raw_data_str.split('\n')
        data_sets_list = [line for line in raw_data if len(line) > 0]
        data = [str.split(line, ':') for line in data_sets_list]
        return data

    def _remove_ignored_data_fields(self, dataset_json):
        return {key: value for (key, value) in dataset_json.items() if key not in self._ignored_data_fields}
