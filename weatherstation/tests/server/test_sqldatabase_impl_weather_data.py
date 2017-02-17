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
from remote_weather_access.common.datastructures import WeatherStationMetadata, WeatherStationDataset, BaseStationSensorData
from remote_weather_access.server._sqldatabase_impl import _WeatherStationTable, _WeatherDataTable
from remote_weather_access.server.exceptions import NotExistingError


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


def database_object():
    """Test database factory"""
    db_file_path = "./tests/workingDir/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name
    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    return sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


class WeatherDataset(object):
    """Test object builder"""
    def __init__(self):
        self._time = datetime.datetime(2016, 12, 15, 13, 30, 45)
        self._pressure = 1308.5
        self._uv = 5.7

    def with_time(self, time):
        self._time = time
        return self

    def with_pressure(self, pressure):
        self._pressure = pressure
        return self

    def with_uv(self, uv):
        self._uv = uv
        return self

    def build(self):
        weather_dataset = WeatherStationDataset(self._time)
        base_station_sensor_data = BaseStationSensorData(
            self._pressure,
            self._uv
        )
        weather_dataset.add_sensor(base_station_sensor_data)

        return weather_dataset


def weather_data_object():
    """Test object factory"""
    return WeatherDataset()


class TestSQLWeatherDataTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()
        self._station_id = "TES"
        weather_station_table = _WeatherStationTable(self._sql)
        weather_station_table.add(
            WeatherStationMetadata(self._station_id, "Device 1", "Location 1", 60.4, -39.9, 121.2, 1.0)
        )

    def tearDown(self):
        self._sql.close()

    def test_add_weather_data(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)
            got_times, got_sensor_data = weather_data_table.get_data(
                self._station_id, some_time_before(), some_time_afterwards()
            )

        # then:
            for got_data_line, data_line in zip(got_sensor_data, weather_data):
                self.assertEqual(got_data_line, data_line.get_sensor_object(BaseStationSensorData.BASE_STATION))

    def test_add_empty_weather_data(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, [])
            got_times, got_sensor_data = weather_data_table.get_data(
                self._station_id, some_time_before(), some_time_afterwards()
            )

        # then:
            self.assertTrue(not got_times)
            self.assertTrue(not got_sensor_data)

    def test_add_weather_data_to_not_existing_station(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]

        # when:
        other_station_id = "TES2"

        # then:
        with self._sql:
            self.assertRaises(NotExistingError, weather_data_table.add, other_station_id, weather_data)

    def test_replace_weather_data(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]
        other_weather_data = a(weather_data_object().with_time(some_time()).with_pressure(998.5))

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)
            weather_data_table.replace(self._station_id, other_weather_data)
            got_times, got_weather_data = weather_data_table.get_data(
                self._station_id, some_time_before(), some_time_afterwards()
            )

        # then:
            self.assertEqual(len(got_weather_data), 1)
            self.assertEqual(
                got_weather_data[0],
                other_weather_data.get_sensor_object(BaseStationSensorData.BASE_STATION)
            )

    def test_replace_weather_data_with_invalid_station(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]
        other_weather_data = a(weather_data_object().with_time(some_time()).with_pressure(998.5))

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)

        # then:
            self.assertRaises(NotExistingError, weather_data_table.replace, "TES2", other_weather_data)

    def test_remove_weather_data(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)
            num_removed = weather_data_table.remove(self._station_id, some_time())
            got_times, *rest = weather_data_table.get_data(
                self._station_id, some_time_before(), some_time_afterwards()
            )

        # then:
            self.assertEqual(num_removed, 1)
            self.assertTrue(not got_times)

    def test_remove_not_existing_weather_data(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)
            num_removed = weather_data_table.remove(self._station_id, some_time_afterwards())

        # then:
            self.assertEqual(num_removed, 0)

    def test_get_weather_data_out_of_range(self):
        # given:
        weather_data_table = _WeatherDataTable(self._sql)
        weather_data = [a(weather_data_object().with_time(some_time()))]

        # when:
        with self._sql:
            weather_data_table.add(self._station_id, weather_data)
            got_time, *rest = weather_data_table.get_data(self._station_id, some_time_before(),
                                                          some_other_time_before())

        # then:
            self.assertTrue(not got_time)


if __name__ == '__main__':
    unittest.main()
