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
from multiprocessing import Queue
from time import sleep

from weathernetwork.common.logging import MultiProcessConnector
from tests.builder_acessors import a
from weathernetwork.common.datastructures import BaseStationSensorData, WindSensorData, CombiSensorData, WeatherMessage
from weathernetwork.common.datastructures import WeatherStationDataset
from weathernetwork.common.datastructures import WeatherStationMetadata, RainSensorData
from weathernetwork.server.exceptions import NotExistingError
from weathernetwork.server.interface import IServerSideProxy
from weathernetwork.server.sqldatabase import SQLWeatherDB, SQLDatabaseServiceFactory


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


def station_id():
    return "TES"


def other_station_id():
    return "TES2"


def combi_sensor_id():
    return "OUT1"


class WeatherDataset(object):
    """Test object builder"""
    def __init__(self):
        self._time = some_time()
        self._base_station_sensor_data = BaseStationSensorData(1032.4, 8.5)
        self._wind_sensor_data = WindSensorData(12.4, 43.9, 180.0, 15.2)
        self._combi_sensor_data = CombiSensorData(combi_sensor_id(), 34.9, 89.7, "outside sensor 1")
        self._rain_sensor_data = RainSensorData(
            12.5,
            some_time() - timedelta(minutes=10),
            cumulated_amount=0,
            cumulation_begin_time=some_time()
        )

    def with_time(self, time):
        self._time = time
        return self

    def with_base_station_sensor_data(self, base_station_sensor_data):
        self._base_station_sensor_data = base_station_sensor_data
        return self

    def with_wind_sensor_data(self, wind_sensor_data):
        self._wind_sensor_data = wind_sensor_data
        return self

    def with_combi_sensor_data(self, combi_sensor_data):
        self._combi_sensor_data = combi_sensor_data
        return self

    def with_rain_sensor_data(self, rain_sensor_data):
        self._rain_sensor_data = rain_sensor_data
        return self

    def build(self):
        weather_dataset = WeatherStationDataset(self._time)
        weather_dataset.add_sensor(self._base_station_sensor_data)
        weather_dataset.add_sensor(self._rain_sensor_data)
        weather_dataset.add_sensor(self._wind_sensor_data)
        weather_dataset.add_sensor(self._combi_sensor_data)
        return weather_dataset


def weather_data_object():
    """Test object factory"""
    return WeatherDataset()


def database_object():
    """Test database factory"""
    db_file_path = "../data/unittests/sqltest/"
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = db_file_path + '/' + db_file_name

    os.makedirs(db_file_path, exist_ok=True)  # creates the test directory if required
    if os.path.isfile(db_file):
        os.remove(db_file)  # removes an already existing database file

    sql_database = SQLWeatherDB(db_file)
    sql_database.add_combi_sensor(combi_sensor_id(), "outside sensor 1")
    sql_database.add_station(WeatherStationMetadata(station_id(), "TE923 Mebus", "Test City", 49.234, 11.024, 440, 1.0))

    return sql_database, db_file


class TestSQLWeatherDB(unittest.TestCase):
    def setUp(self):
        self._sql_database, __ = database_object()

    def tearDown(self):
        self._sql_database.close_database()

    def test_add_dataset(self):
        # given:
        data = a(weather_data_object())

        # when:
        self._sql_database.add_dataset(station_id(), data)
        got_data = self._sql_database.get_data_in_time_range(station_id(), some_time_before(), some_time_afterwards())

        # then:
        self.assertEqual(len(got_data), 1)
        self.assertEqual(got_data[0], data)

    def test_add_for_not_existing_station(self):
        # given:
        data = a(weather_data_object())

        # then:
        self.assertRaises(NotExistingError, self._sql_database.add_dataset, other_station_id(), data)

    def test_add_dataset_with_implicit_overwriting(self):
        # given:
        data = a(weather_data_object())
        other_data = a(weather_data_object().with_wind_sensor_data(WindSensorData(120.5, 150.9, 182.3, -0.2)))

        # when:
        self._sql_database.add_dataset(station_id(), data)
        self._sql_database.add_dataset(station_id(), other_data)
        got_data = self._sql_database.get_data_in_time_range(station_id(), some_time_before(), some_time_afterwards())

        # then:
        self.assertEqual(len(got_data), 1)
        self.assertEqual(got_data[0], other_data)

    def test_replace_dataset(self):
        # given:
        data = a(weather_data_object())
        other_data = a(weather_data_object().with_combi_sensor_data(CombiSensorData("OUT1", -1.9, 50.0,
                                                                                    "outside sensor 1")))

        # when:
        self._sql_database.add_dataset(station_id(), data)
        self._sql_database.replace_dataset(station_id(), other_data)
        got_data = self._sql_database.get_data_in_time_range(station_id(), some_time_before(), some_time_afterwards())

        # then:
        self.assertEqual(other_data, got_data[0])

    def test_replace_not_existing_dataset(self):
        # given:
        data = a(weather_data_object())
        other_data = a(weather_data_object().with_combi_sensor_data(CombiSensorData("OUT1", -1.9, 50.0,
                                                                                    "outside sensor 1")))

        # when:
        self._sql_database.add_dataset(station_id(), data)

        # then:
        self.assertRaises(NotExistingError, self._sql_database.replace_dataset, other_station_id(), other_data)

    def test_remove_dataset(self):
        # given:
        data = a(weather_data_object())

        # when:
        self._sql_database.add_dataset(station_id(), data)
        self._sql_database.remove_dataset(station_id(), data.get_time())

        # then:
        self.assertFalse(self._sql_database.get_data_in_time_range(
            station_id(), some_time_before(), some_time_afterwards()
        ))


class MockServerSideProxy(IServerSideProxy):
    def __init__(self):
        self._finished_id = None

    def acknowledge_persistence(self, finished_id, logger):
        self._finished_id = finished_id

    def get_finished_id(self):
        return self._finished_id


class TestSQLDatabaseService(unittest.TestCase):
    def setUp(self):
        self._sql_database, self._db_file = database_object()

    def tearDown(self):
        self._sql_database.close_database()

    def test_add_data(self):
        # given:
        dummy_logger_connector = MultiProcessConnector(Queue(), 1)
        database_service = SQLDatabaseServiceFactory(self._db_file, dummy_logger_connector).create(True)
        server_side_proxy_mock = MockServerSideProxy()
        database_service.register_observer(server_side_proxy_mock)

        # when:
        message_id = "messageID"
        message = WeatherMessage(message_id, station_id(), a(weather_data_object()))
        database_service.add_data(message)

        # then:
        sleep(1)
        self.assertEqual(server_side_proxy_mock.get_finished_id(), message_id)

        database_service.unregister_observer(server_side_proxy_mock)


if __name__ == '__main__':
    unittest.main()
