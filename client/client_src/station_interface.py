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
import logging
import os
from datetime import datetime, timedelta
from json import JSONDecodeError
from shutil import copyfile

import numpy as np
import pytz

from .rest_client import ServerProxy
from .utils import IsoDateTimeJSONEncoder, IsoDateTimeJSONDecoder

# the weather station reader tool must be called using root privileges
WEATHER_STATION_READER_PATH = 'sudo /opt/weatherstation/te923tool-0.6.1/te923con'

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
    DATA_FILE_PATH = r'last_known_station_data.json'
    BACKUP_FILE_PATH = DATA_FILE_PATH + '.backup'
    _instance = None

    def __init__(self):
        if LastKnownStationData._instance is not None:
            raise AssertionError('This class is a singleton')
        else:
            LastKnownStationData._instance = self

        self._last_read_utc_time_point = datetime.min
        self._read_from_disk()

    @staticmethod
    def get():
        if LastKnownStationData._instance is None:
            LastKnownStationData()

        return LastKnownStationData._instance

    def get_utc_time_point(self):
        return self._last_read_utc_time_point

    def set_utc_time_point(self, last_local_time_point):
        self._last_read_utc_time_point = last_local_time_point.astimezone(pytz.UTC)
        self._write_to_disk()

    def _write_to_disk(self):
        # if the file will get corrupt later, the copy is guaranteed to be valid
        try:
            copyfile(self.DATA_FILE_PATH, self.BACKUP_FILE_PATH)
        except FileNotFoundError:
            pass

        with open(self.DATA_FILE_PATH, 'w') as file:
            json.dump({
                'last_utc_time_point': self._last_read_utc_time_point
            }, file, cls=IsoDateTimeJSONEncoder)

    def _read_from_disk(self):
        try:
            self._perform_read_from_disk(self.DATA_FILE_PATH, do_fail_on_not_existing=False)
        except (JSONDecodeError, KeyError):
            # the file was corrupt
            self._perform_read_from_disk(self.BACKUP_FILE_PATH, do_fail_on_not_existing=True)

            # correct the file and backup
            self._write_to_disk()
            os.remove(self.BACKUP_FILE_PATH)

    def _perform_read_from_disk(self, file_path, do_fail_on_not_existing):
        try:
            with open(file_path, 'r') as file:
                read_data = json.load(file, cls=IsoDateTimeJSONDecoder)
                self._last_read_utc_time_point = read_data['last_utc_time_point'].astimezone(pytz.UTC)
        except FileNotFoundError:
            if do_fail_on_not_existing:
                raise
            else:
                self._last_read_utc_time_point = datetime.min


class WeatherStationProxy(object):
    _TIME_TOLERANCE_IN_MIN = timedelta(minutes=10)

    def __init__(self, config, read_period_in_minutes):
        self._server_proxy = ServerProxy(config)
        self._station_id = config['station_id']
        self._local_time_zone = pytz.timezone(config['time_zone'])
        self._read_period_in_minutes = read_period_in_minutes
        self._ignored_data_fields = config['ignored_data_fields']

    def read_and_send(self):
        last_read_utc_time_point = LastKnownStationData.get().get_utc_time_point()
        time_difference = datetime.utcnow().astimezone(pytz.UTC) - last_read_utc_time_point
        if time_difference < 2 * timedelta(minutes=self._read_period_in_minutes):
            is_read_all_datasets = False
        else:
            is_read_all_datasets = True

        json_data = self._perform_read_data(is_read_all_datasets)
        self._server_proxy.send_data(json_data, self._station_id)

        # the data is guaranteed to be persisted on the server now
        if len(json_data) > 0:
            last_read_utc_time_point = json_data[-1]['timepoint']
            LastKnownStationData.get().set_utc_time_point(last_read_utc_time_point)
            logging.info('Read and sent data to backend successfully until {}'.format(last_read_utc_time_point))
        else:
            logging.info('No new data to be sent to backend')

    def _perform_read_data(self, is_read_all_datasets):
        if is_read_all_datasets:
            raw_data = os.popen(WEATHER_STATION_READER_PATH + ' -b')
        else:
            raw_data = os.popen(WEATHER_STATION_READER_PATH)

        if not raw_data:
            raise ConnectionError('No connection to the weather station was possible.')

        data = self._parse_raw_data(raw_data)
        data = self._to_float_or_nan(data)

        json_data = self._to_json(data)
        json_data = self._replace_potentially_wrong_time_stamp(json_data, is_read_all_datasets)
        json_data = self._remove_time_points_from_the_future(json_data)
        json_data = self._filter_out_already_read_time_points(json_data, is_read_all_datasets)

        return json_data

    def _to_json(self, data):
        json_data = []

        for dataset in data:
            local_time = self._local_time_zone.localize(datetime.fromtimestamp(int(dataset[TIME])), is_dst=True)

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
            json_data.append(self._replace_nan_by_zero(dataset_json))

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
    def _replace_nan_by_zero(dataset_json: dict):
        for key, value in dataset_json.items():
            if isinstance(value, float) and np.isnan(value):
                dataset_json[key] = 0

        return dataset_json

    @staticmethod
    def _to_temp_humid_json(dataset, sensor_id, temp_index, humid_index):
        temperature = dataset[temp_index]
        humidity = dataset[humid_index]
        if np.isnan(temperature) and np.isnan(humidity):
            return {}
        else:
            return {
                'sensor_id': sensor_id,
                'temperature': temperature if not np.isnan(temperature) else 0,
                'humidity': humidity if not np.isnan(humidity) else 0
            }

    @staticmethod
    def _to_float_or_nan(data):
        # invalid data is marked by 'i'
        for index, dataset in enumerate(data):
            data[index] = [np.nan if entry == 'i' else float(entry) for entry in dataset]
        return data

    def _replace_potentially_wrong_time_stamp(self, json_data, is_read_all_datasets):
        if not is_read_all_datasets:
            # the time-stamp provided by "last time point" requests from the station can be wrong
            json_data[0]['timepoint'] = datetime.now(tz=self._local_time_zone)
        return json_data

    def _remove_time_points_from_the_future(self, json_data):
        # the station may provide time points lying in the future
        curr_time = datetime.now(tz=self._local_time_zone)
        json_data = [entry for entry in json_data if
                     entry['timepoint'] < (curr_time + WeatherStationProxy._TIME_TOLERANCE_IN_MIN)]
        return json_data

    def _filter_out_already_read_time_points(self, json_data, is_read_all_datasets):
        # the station returns all data available in the memory, but a part of that had already been read earlier
        if is_read_all_datasets:
            last_read_utc_time_point = LastKnownStationData.get().get_utc_time_point()
            local_last_read_dataset_time = last_read_utc_time_point.replace(tzinfo=pytz.utc)
            local_last_read_dataset_time.astimezone(self._local_time_zone)
            json_data = [entry for entry in json_data if entry['timepoint'] > local_last_read_dataset_time]
        return json_data

    @staticmethod
    def _parse_raw_data(output_stream):
        data_sets_list = [line.strip() for line in output_stream]
        data = [str.split(line, ':') for line in data_sets_list]
        return data

    def _remove_ignored_data_fields(self, dataset_json):
        return {key: value for (key, value) in dataset_json.items() if key not in self._ignored_data_fields}
