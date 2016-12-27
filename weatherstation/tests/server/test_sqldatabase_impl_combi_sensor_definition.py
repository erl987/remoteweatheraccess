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


def some_sensor_id():
    return "OUT1"


def some_description():
    return "Outdoor sensor 1"


def some_other_sensor_id():
    return "OUT2"


def some_other_description():
    return "Alternative description"


def database_object():
    """Test database factory"""
    db_file_path = "./data/unittests/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name
    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    return sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)


class TestSQLCombiSensorDefinitionTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()

    def tearDown(self):
        self._sql.close()

    def test_add_combi_sensor(self):
        # given:
        combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)

        # when:
        with self._sql:
            combi_sensor_definition_table.add(some_sensor_id(), some_description())
            combi_sensor_definition_table.add(some_other_sensor_id(), some_other_description())
            got_sensor_definitions = combi_sensor_definition_table.get_combi_sensor_ids()
            got_sensor_descriptions = combi_sensor_definition_table.get_sensor_descriptions()  # type: dict

        # then:
            self.assertEqual(got_sensor_definitions, [some_sensor_id(), some_other_sensor_id()])
            self.assertEqual(set(got_sensor_descriptions.values()), {some_description(), some_other_description()})

    def test_add_already_existing_combi_sensor(self):
        # given:
        combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)

        # when:
        with self._sql:
            combi_sensor_definition_table.add(some_sensor_id(), some_description())

        # then:
            self.assertRaises(AlreadyExistingError, combi_sensor_definition_table.add,
                              some_sensor_id(), some_description())

    def test_replace_combi_sensor(self):
        # given:
        combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)

        # when:
        with self._sql:
            combi_sensor_definition_table.add(some_sensor_id(), some_description())
            combi_sensor_definition_table.replace(some_sensor_id(), some_other_description())

            got_sensor_definitions = combi_sensor_definition_table.get_combi_sensor_ids()
            got_sensor_descriptions = combi_sensor_definition_table.get_sensor_descriptions()  # type: dict

        # then:
            self.assertEqual(got_sensor_definitions, [some_sensor_id()])
            self.assertEqual(set(got_sensor_descriptions.values()), {some_other_description()})

    def test_replace_not_existing_combi_sensor(self):
        # given:
        combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)

        # when:
        with self._sql:
            combi_sensor_definition_table.add(some_sensor_id(), some_description())

        # then:
            self.assertRaises(NotExistingError, combi_sensor_definition_table.replace,
                              some_other_sensor_id(), some_other_description())

    def test_remove_combi_sensor(self):
        # given:
        combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)

        # when:
        with self._sql:
            combi_sensor_definition_table.add(some_sensor_id(), some_description())
            combi_sensor_definition_table.remove(some_sensor_id())

        # then:
            self.assertFalse(combi_sensor_definition_table.exists(some_sensor_id()))

if __name__ == '__main__':
    unittest.main()
