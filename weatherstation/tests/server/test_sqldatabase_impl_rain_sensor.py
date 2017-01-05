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
from datetime import timedelta

from tests.builder_acessors import *
from weathernetwork.common.datastructures import WeatherStationDataset, RainSensorData
from weathernetwork.server._sqldatabase_impl import _RainSensorTable
from weathernetwork.server.exceptions import NotExistingError, AlreadyExistingError


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


class RainSensorDataset:
    """Test object builder"""
    def __init__(self):
        self._time = datetime.datetime(2016, 12, 15, 13, 30, 45)
        self._amount = 9.6
        self._begin_time = self._time - timedelta(minutes=10)

    def with_end_time(self, time):
        self._time = time
        self._begin_time = time - timedelta(minutes=10)
        return self

    def with_begin_time(self, time):
        self._begin_time = time
        return self

    def with_amount(self, amount):
        self._amount = amount
        return self

    def build(self):
        weather_dataset = WeatherStationDataset(self._time)
        rain_sensor_data = RainSensorData(
            self._amount,
            self._begin_time
        )
        weather_dataset.add_sensor(rain_sensor_data)

        return weather_dataset


def rain_sensor_object():
    """Test object factory"""
    return RainSensorDataset()


def database_object():
    """Test database factory"""
    db_file_path = "./data/unittests/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name
    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    return sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


class TestSQLRainSensorTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()

    def tearDown(self):
        self._sql.close()

    def test_add_rain_sensor_data(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time())),
                       a(rain_sensor_object().with_end_time(some_time() + timedelta(minutes=10)))]

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)
            got_sensor_data = rain_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())

        # then:
            is_first = True
            cumulated = 0
            for sensor_data_line, got_sensor_data_line in zip(sensor_data, got_sensor_data):
                amount = sensor_data_line.get_sensor_value([RainSensorData.RAIN, RainSensorData.PERIOD])
                self.assertEqual(amount, got_sensor_data_line.get_sensor_value(RainSensorData.PERIOD))
                if not is_first:
                    cumulated += amount

                self.assertEqual(cumulated, got_sensor_data_line.get_sensor_value(RainSensorData.CUMULATED))
                is_first = False

    def test_add_empty_rain_sensor_data(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, [])
            got_sensor_data = rain_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())

        # then:
            self.assertTrue(not got_sensor_data)

    def test_add_rain_sensor_data_with_invalid_begin_time(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"

        # when:
        invalid_sensor_data = \
            [a(rain_sensor_object().with_end_time(some_time()).with_begin_time(some_time_afterwards()))]

        # then:
        with self._sql:
            self.assertRaises(ValueError, rain_sensor_table.add, station_id, invalid_sensor_data)

    def test_add_overlapping_rain_sensor_data(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time()))]

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)

        # then:
            self.assertRaises(AlreadyExistingError, rain_sensor_table.add, station_id, sensor_data)

    def test_replace_rain_sensor_data(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time()))]
        other_sensor_data = a(rain_sensor_object().with_amount(3.9).with_end_time(some_time()))

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)
            rain_sensor_table.replace(station_id, other_sensor_data)
            got_sensor_data = rain_sensor_table.get_data(station_id, some_time_before(), some_time_afterwards())

        # then:
        for other_sensor_data_line, got_sensor_data_line in zip([other_sensor_data], got_sensor_data):
            amount = other_sensor_data_line.get_sensor_value([RainSensorData.RAIN, RainSensorData.PERIOD])
            self.assertEqual(amount, got_sensor_data_line.get_sensor_value(RainSensorData.PERIOD))

    def test_replace_rain_sensor_data_with_invalid_station(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time()))]
        other_sensor_data = a(rain_sensor_object().with_amount(3.9).with_end_time(some_time()))

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)

        # then:
            self.assertRaises(NotExistingError, rain_sensor_table.replace, "TES2", other_sensor_data)

    def test_get_rain_sensor_data_out_of_range(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time()))]

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)
            got_sensor_data = rain_sensor_table.get_data(station_id, some_time_before(), some_other_time_before())

        # then:
            self.assertTrue(not got_sensor_data)

    def test_get_rain_sensor_data_with_invalid_station(self):
        # given:
        rain_sensor_table = _RainSensorTable(self._sql)
        station_id = "TES"
        sensor_data = [a(rain_sensor_object().with_end_time(some_time()))]

        # when:
        with self._sql:
            rain_sensor_table.add(station_id, sensor_data)
            got_sensor_data = rain_sensor_table.get_data("TES2", some_time_before(), some_time_afterwards())

            # then:
            self.assertTrue(not got_sensor_data)


if __name__ == '__main__':
    unittest.main()
