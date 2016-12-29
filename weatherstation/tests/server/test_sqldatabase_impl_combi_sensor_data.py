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

import os
import sqlite3
import unittest
import datetime
from datetime import timedelta

from tests.builder_acessors import *
from weathernetwork.common.datastructures import WeatherStationMetadata, WeatherStationDataset, WindSensorData, \
    RainSensorData, CombiSensorData, BaseStationSensorData
from weathernetwork.server._sqldatabase_impl import _WeatherStationTable, _WindSensorTable, _RainSensorTable, \
    _CombiSensorDataTable, _CombiSensorDefinitionTable, _WeatherDataTable
from weathernetwork.server.exceptions import NotExistingError, AlreadyExistingError


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


class CombiSensorDataset:
    """Test object builder"""
    def __init__(self):
        self._time = datetime.datetime(2016, 12, 15, 13, 30, 45)
        self._sensor_id = "OUT1"
        self._description = "outdoor sensor 1"
        self._temperature = 23.5
        self._humidity = 89.3

    def with_time(self, time):
        self._time = time
        return self

    def with_sensor_id(self, sensor_id):
        self._sensor_id = sensor_id
        return self

    def with_description(self, description):
        self._description = description
        return self

    def with_temperature(self, temperature):
        self._temperature = temperature
        return self

    def with_humidity(self, humidity):
        self._humidity = humidity
        return self

    def build(self):
        weather_dataset = WeatherStationDataset(self._time)
        combi_sensor_data = CombiSensorData(
            self._sensor_id,
            self._temperature,
            self._humidity,
            self._description
        )
        weather_dataset.add_sensor(combi_sensor_data)

        return weather_dataset


def combi_sensor_object():
    """Test object factory"""
    return CombiSensorDataset()


def database_object():
    """Test database factory"""
    db_file_path = "./data/unittests/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name
    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    return sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


class TestSQLCombiSensorDataTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()
        self._sensor_id = "OUT1"
        self._description = "outdoor sensor 1"
        self._station_id = "TES"
        self._combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)
        self._combi_sensor_definition_table.add(self._sensor_id, self._description)
        self._combi_sensor_definition_table.add("OUT2", "outdoor sensor 2")

    def tearDown(self):
        self._sql.close()

    def test_add_combi_sensor_data(self):
        # given:
        combi_sensor_table = _CombiSensorDataTable(self._sql)
        sensor_data = [a(combi_sensor_object().with_time(some_time()).with_description(self._description))]

        with self._sql:
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

        # when:
            combi_sensor_table.add(self._station_id, available_combi_sensor_ids, combi_sensor_descriptions, sensor_data)
            got_sensor_data = combi_sensor_table.get_data_at_time(
                self._station_id, some_time(), combi_sensor_descriptions)

        # then:
            for got_sensor_data_line, sensor_data_line in zip(got_sensor_data, sensor_data):
                self.assertEqual(got_sensor_data_line, sensor_data_line.get_sensor_object(self._sensor_id))

    def test_replace_combi_sensor_data(self):
        # given:
        combi_sensor_table = _CombiSensorDataTable(self._sql)
        sensor_data = [a(combi_sensor_object().with_time(some_time()).with_description(self._description))]
        other_sensor_dataset = a(combi_sensor_object().with_time(some_time()).with_temperature(-2.3).
                                 with_description(self._description))

        with self._sql:
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

        # when:
            combi_sensor_table.add(self._station_id, available_combi_sensor_ids, combi_sensor_descriptions, sensor_data)
            combi_sensor_table.replace(self._station_id, other_sensor_dataset, available_combi_sensor_ids,
                                       combi_sensor_descriptions)
            got_sensor_data = combi_sensor_table.get_data_at_time(self._station_id, some_time(),
                                                                  combi_sensor_descriptions)

        # then:
            self.assertEqual(got_sensor_data[0], other_sensor_dataset.get_sensor_object(self._sensor_id))

    def test_replace_combi_sensor_data_with_invalid_station(self):
        # given:
        combi_sensor_table = _CombiSensorDataTable(self._sql)
        sensor_data = [a(combi_sensor_object().with_time(some_time()).with_description(self._description))]
        other_sensor_dataset = a(combi_sensor_object().with_time(some_time()).with_temperature(-2.3).
                                 with_description(self._description))

        with self._sql:
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

        # when:
            other_station_id = "TES2"
            combi_sensor_table.add(self._station_id, available_combi_sensor_ids, combi_sensor_descriptions, sensor_data)

        # then:
            self.assertRaises(NotExistingError, combi_sensor_table.replace, other_station_id, other_sensor_dataset,
                              available_combi_sensor_ids, combi_sensor_descriptions)

    def test_get_combi_sensor_data_with_invalid_station(self):
        # given:
        combi_sensor_table = _CombiSensorDataTable(self._sql)
        sensor_data = [a(combi_sensor_object().with_time(some_time()).with_description(self._description))]

        with self._sql:
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

        # when:
            other_station_id = "TES2"
            combi_sensor_table.add(self._station_id, available_combi_sensor_ids, combi_sensor_descriptions, sensor_data)
            got_sensor_data = combi_sensor_table.get_data_at_time(other_station_id, some_time(),
                                                                  combi_sensor_descriptions)

        # then:
            self.assertTrue(not got_sensor_data)


if __name__ == '__main__':
    unittest.main()
