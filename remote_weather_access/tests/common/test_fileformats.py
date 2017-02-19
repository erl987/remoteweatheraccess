# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>

import datetime
import os
import unittest
from datetime import timedelta

import shutil

from tests.builder_acessors import a
from remote_weather_access.common.datastructures import RainSensorData, BaseStationSensorData, WindSensorData, CombiSensorData
from remote_weather_access.common.datastructures import WeatherStationMetadata, WeatherStationDataset
from remote_weather_access.common.exceptions import DatasetFormatError, PCWetterstationFileParseError
from remote_weather_access.common.fileformats import PCWetterstationFormatFile


def station_id():
    return "TES2"


def combi_sensor_ids():
    return ["OUT1"]


def combi_sensor_descriptions():
    return {"OUT1": "outside sensor 1"}


def data_file_path():
    return "./tests/workingDir/fileformats"


class StationMetadata(object):
    """Test object builder"""
    def __init__(self):
        self._station_id = station_id()
        self._device_info = "Test weather station"
        self._location_info = "Test place"
        self._latitude = -59.3
        self._longitude = -18.5
        self._height = 203
        self._rain_calib_factor = 1.0

    def with_station_id(self, new_station_id):
        self._station_id = new_station_id
        return self

    def build(self):
        metadata = WeatherStationMetadata(
            self._station_id,
            self._device_info,
            self._location_info,
            self._latitude,
            self._longitude,
            self._height,
            self._rain_calib_factor
        )
        return metadata


def station_metadata_object():
    return StationMetadata()


class Data(object):
    """Test object builder"""
    def __init__(self):
        self._time = datetime.datetime(year=2016, month=9, day=30, hour=23, minute=40)
        self._base_station_sensor_data = BaseStationSensorData(1032.4, 8.5)
        self._wind_sensor_data = WindSensorData(12.4, 43.9, 180.0, 15.2)
        sensor_id = combi_sensor_ids()[0]
        self._combi_sensor_data = CombiSensorData(sensor_id, 34.9, 89.7, combi_sensor_descriptions()[sensor_id])

        self._rain_sensor_data = [
            RainSensorData(12.5, self._time - timedelta(minutes=10)),
            RainSensorData(10.5, self._time),
            RainSensorData(9.2, self._time + timedelta(minutes=10)),
            RainSensorData(15.5, self._time + 2 * timedelta(minutes=10))
            ]

    def without_wind_sensor(self):
        self._wind_sensor_data = None
        return self

    def build(self):
        time = self._time
        data = []
        for index in range(0, 4):
            dataset = WeatherStationDataset(time)
            dataset.add_sensor(self._base_station_sensor_data)
            dataset.add_sensor(self._rain_sensor_data[index])
            if self._wind_sensor_data:
                dataset.add_sensor(self._wind_sensor_data)
            dataset.add_sensor(self._combi_sensor_data)

            data.append(dataset)
            time += timedelta(minutes=10)

        return data


def data_object():
    return Data()


def remove_line_from_file(target_file_name, line_number_to_be_deleted):
    file = open(target_file_name, mode="r+", encoding='latin-1')
    content = file.readlines()
    file.seek(0)
    line_number = 1
    for line in content:
        if line_number != line_number_to_be_deleted:
            file.write(line)
        line_number += 1
    file.truncate()
    file.close()


def _find_first_month(data):
    """It is assumed that the whole data is from one year and in ascending order"""
    first_month = None
    counter = 0
    for dataset in data:
        curr_month = datetime.datetime(day=1, month=dataset.get_time().month, year=dataset.get_time().year)
        if not first_month:
            first_month = curr_month

        if curr_month != first_month:
            break
        counter += 1

    first_month_data = data[0:counter]
    first_month_file_name = "EXP" + first_month.strftime('%m_%y') + ".csv"

    return first_month_data, first_month_file_name


class TestPCWetterstationFormatFile(unittest.TestCase):
    def setUp(self):
        if os.path.isdir(data_file_path()):
            shutil.rmtree(data_file_path(), ignore_errors=True)
        os.makedirs(data_file_path(), exist_ok=True)  # creates the test directory if required

    def tearDown(self):
        pass

    def test_read_write(self):
        # given:
        weather_data_file = PCWetterstationFormatFile(combi_sensor_ids(), combi_sensor_descriptions())
        first_month_data, first_month_file_name = _find_first_month(a(data_object()))

        # when:
        weather_data_file.write(
            data_file_path(), a(data_object()), a(station_metadata_object())
        )
        got_data, got_rain_counter_base, got_station_metadata = weather_data_file.read(
            data_file_path() + "/" + first_month_file_name, station_id())

        # then:
        self.assertEqual(got_data, first_month_data)
        self.assertEqual(got_station_metadata, a(station_metadata_object()))

    def test_write_with_not_existing_sensor(self):
        # given:
        weather_data_file = PCWetterstationFormatFile(combi_sensor_ids(), combi_sensor_descriptions())

        # when:
        data = a(data_object().without_wind_sensor())

        # then
        self.assertRaises(DatasetFormatError,
                          weather_data_file.write, data_file_path(), data, a(station_metadata_object())
                          )

    def test_read_not_existing_file(self):
        # given:
        weather_data_file = PCWetterstationFormatFile(combi_sensor_ids(), combi_sensor_descriptions())

        # then:
        self.assertRaises(FileNotFoundError, weather_data_file.read, "invalidFileName.dat", station_id())

    def test_read_invalid_file_format(self):
        # given:
        weather_data_file = PCWetterstationFormatFile(combi_sensor_ids(), combi_sensor_descriptions())
        first_month_data, first_month_file_name = _find_first_month(a(data_object()))

        # when:
        weather_data_file.write(
            data_file_path(), a(data_object()), a(station_metadata_object())
        )
        remove_line_from_file(data_file_path() + "/" + first_month_file_name, 3)

        # then:
        self.assertRaises(PCWetterstationFileParseError,
                          weather_data_file.read, data_file_path() + "/" + first_month_file_name, station_id())

    def test_delete_datafiles(self):
        # given:
        data_file_list = ["test_1.txt", "test_2.txt"]
        for data_file_name in data_file_list:
            with open(data_file_path() + os.sep + data_file_name, 'w+') as file:
                file.write("TEST")

        # when:
        PCWetterstationFormatFile.delete_datafiles(data_file_path(), data_file_list)

        # then:
        self.assertFalse(os.listdir(data_file_path()))

if __name__ == '__main__':
    unittest.main()
