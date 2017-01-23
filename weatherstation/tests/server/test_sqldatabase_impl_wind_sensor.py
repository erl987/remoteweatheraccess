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
import sqlite3
import unittest

from tests.builder_acessors import *
from weathernetwork.common.datastructures import WeatherStationDataset, WindSensorData
from weathernetwork.server._sqldatabase_impl import _WindSensorTable


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


class WindSensorDataset(object):
    """Test object builder"""
    def __init__(self):
        self._time = datetime.datetime(2016, 12, 15, 13, 30, 45)
        self._average = 5.0
        self._gusts = 12.5
        self._direction = 190.5
        self._wind_chill = 19.5

    def with_time(self, time):
        self._time = time
        return self

    def with_average(self, average):
        self._average = average
        return self

    def with_gusts(self, gusts):
        self._gusts = gusts
        return self

    def with_direction(self, direction):
        self._direction = direction
        return self

    def with_wind_chill(self, wind_chill):
        self._wind_chill = wind_chill
        return self

    def build(self):
        weather_dataset = WeatherStationDataset(self._time)
        wind_sensor_data = WindSensorData(
            self._average,
            self._gusts,
            self._direction,
            self._wind_chill
        )
        weather_dataset.add_sensor(wind_sensor_data)

        return weather_dataset


def wind_sensor_object():
    """Test object factory"""
    return WindSensorDataset()


def database_object():
    """Test database factory"""
    db_file_path = "../data/unittests/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name
    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    return sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


class TestSQLWindSensorTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()

    def tearDown(self):
        self._sql.close()

    def test_add_wind_sensor_data(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(wind_sensor_object().with_time(some_time()))]

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, sensor_data)
            got_sensor_data = wind_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())

        # then:
            for got_data_line, data_line in zip(got_sensor_data, sensor_data):
                self.assertEqual(got_data_line, data_line.get_sensor_object(WindSensorData.WIND))

    def test_add_empty_wind_sensor_data(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, [])
            got_sensor_data = wind_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())

        # then:
            self.assertTrue(not got_sensor_data)

    def test_replace_wind_sensor_data(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(wind_sensor_object().with_time(some_time()))]
        other_sensor_data = a(wind_sensor_object().with_average(98.5).with_time(some_time()))

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, sensor_data)
            wind_sensor_table.replace(station_id, other_sensor_data)

        # then:
            got_sensor_data = wind_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())
            self.assertEqual(len(got_sensor_data), 1)
            self.assertEqual(other_sensor_data.get_sensor_object(WindSensorData.WIND), got_sensor_data[0])

    def test_replace_wind_sensor_data_with_invalid_station(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(wind_sensor_object().with_time(some_time()))]
        other_sensor_data = a(wind_sensor_object().with_time(some_time()))

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, sensor_data)
            wind_sensor_table.replace("TES2", other_sensor_data)

        # then:
            got_sensor_data = wind_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())
            self.assertEqual(len(got_sensor_data), 1)
            self.assertEqual(sensor_data[0].get_sensor_object(WindSensorData.WIND), got_sensor_data[0])  # original data

    def test_get_data_wind_sensor_data_out_of_range(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(wind_sensor_object().with_time(some_time()))]

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, sensor_data)
            got_sensor_data = wind_sensor_table.get_data(station_id, some_time_before(), some_other_time_before())

        # then:
            self.assertTrue(not got_sensor_data)

    def test_get_data_wind_sensor_with_invalid_station(self):
        # given:
        wind_sensor_table = _WindSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(wind_sensor_object().with_time(some_time()))]

        # when:
        with self._sql:
            wind_sensor_table.add(station_id, sensor_data)
            got_sensor_data = wind_sensor_table.get_data("TES2", some_time_before(), some_time_afterwards())

        # then:
            self.assertTrue(not got_sensor_data)

if __name__ == '__main__':
    unittest.main()
