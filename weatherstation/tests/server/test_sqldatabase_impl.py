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
    RainSensorData
from weathernetwork.server._sqldatabase_impl import _WeatherStationTable, _WindSensorTable, _RainSensorTable
from weathernetwork.server.exceptions import NotExistingError, AlreadyExistingError


def some_time():
    return datetime.datetime(2016, 11, 10, 19, 20, 15)


def some_time_before():
    return datetime.datetime(2016, 11, 1, 0, 0, 0)


def some_other_time_before():
    return datetime.datetime(2016, 11, 3, 15, 30, 15)


def some_time_afterwards():
    return datetime.datetime(2016, 12, 1, 0, 0, 0)


class Station:
    """Test object builder"""
    def __init__(self):
        self._station_id = "DEFAULT"
        self._device = "Test device"
        self._location = "Test City"
        self._latitude = -48.3
        self._longitude = -179.5
        self._height = -2.1
        self._rain_calib_factor = 1.1

    def with_station_id(self, station_id):
        self._station_id = station_id
        return self

    def with_device(self, device):
        self._device = device
        return self

    def with_location(self, location):
        self._location = location
        return self

    def with_latitude(self, latitude):
        self._latitude = latitude
        return self

    def with_longitude(self, longitude):
        self._longitude = longitude
        return self

    def with_height(self, height):
        self._height = height
        return self

    def with_rain_calib_factor(self, rain_calib_factor):
        self._rain_calib_factor = rain_calib_factor
        return self

    def build(self):
        station = WeatherStationMetadata(
            self._station_id,
            self._device,
            self._location,
            self._latitude,
            self._longitude,
            self._height,
            self._rain_calib_factor
        )

        return station


def station_object():
    """Test object factory"""
    return Station()


class WindSensorDataset:
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


class TestSQLWeatherStationTable(unittest.TestCase):
    def setUp(self):
        self._sql = database_object()

    def tearDown(self):
        self._sql.close()

    def test_exists_with_existing_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        station = a(station_object().with_station_id(station_id))

        # when:
        with self._sql:
            weather_station_table.add(station)

        # then:
        self.assertEqual(weather_station_table.exists(station_id), True)

    def test_exists_with_non_existing_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        other_station_id = "TES2"

        # when:
        with self._sql:
            weather_station_table.add(a(station_object()))

        # then:
            self.assertEqual(weather_station_table.exists(other_station_id), False)

    def test_replace_after_adding_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        other_station = a(station_object().
                          with_station_id(station_id).
                          with_device("other device").
                          with_latitude(28.3).
                          with_longitude(38.2).
                          with_height(490.5).
                          with_location("Location").
                          with_rain_calib_factor(1.0))

        # when:
        with self._sql:
            weather_station_table.add(a(station_object().with_station_id(station_id)))
            weather_station_table.replace(other_station)

        # then:
            got_station = weather_station_table.get_metadata(station_id)
            self.assertEqual(got_station, other_station)

    def test_replace_with_not_existing_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        other_station_id = "TES2"
        completely_other_station = a(station_object().with_station_id(other_station_id))

        # when:
        with self._sql:
            weather_station_table.add(a(station_object()))

        # then:
            self.assertRaises(NotExistingError, weather_station_table.replace, completely_other_station)

    def test_add_new_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        station = a(station_object().with_station_id(station_id))

        # when:
        with self._sql:
            weather_station_table.add(station)

        # then:
            got_station = weather_station_table.get_metadata(station_id)
            self.assertEqual(got_station, station)

    def test_add_already_existing_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)

        # when:
        with self._sql:
            weather_station_table.add(a(station_object()))

        # then:
            self.assertRaises(AlreadyExistingError,  weather_station_table.add, a(station_object()))

    def test_remove_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        station = a(station_object().with_station_id(station_id))

        # when:
        with self._sql:
            weather_station_table.add(station)

        # then:
            self.assertTrue(weather_station_table.remove(station_id))
            self.assertFalse(weather_station_table.exists(station_id))

    def test_remove_with_not_existing_station(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        other_station_id = "TES2"
        other_station = a(station_object().with_station_id(other_station_id))

        # when:
        with self._sql:
            weather_station_table.add(other_station)  # another station is added

        # then:
            self.assertFalse(weather_station_table.remove(station_id))
            self.assertTrue(weather_station_table.exists(other_station_id))

    def test_get_metadata(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        station = a(station_object().with_station_id(station_id))

        # when:
        with self._sql:
            weather_station_table.add(station)

        # then:
            got_station = weather_station_table.get_metadata(station_id)
            self.assertEqual(got_station, station)

    def test_get_metadata_of_not_existing_station(self):
        # given
        weather_station_table = _WeatherStationTable(self._sql)

        # when:
        with self._sql:
            station_id = "TES"

        # then:
            self.assertRaises(NotExistingError, weather_station_table.get_metadata, station_id)


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
                got_amount = got_sensor_data_line.get_sensor_value([RainSensorData.RAIN, RainSensorData.PERIOD])
                got_cumulated = got_sensor_data_line.get_sensor_value([RainSensorData.RAIN, RainSensorData.CUMULATED])
                if not is_first:
                    cumulated += amount

                self.assertEqual(cumulated, got_cumulated)
                self.assertEqual(amount, got_amount)
                self.assertEqual(sensor_data_line.get_time(), got_sensor_data_line.get_time())
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
            other_amount = other_sensor_data.get_sensor_value([RainSensorData.RAIN, RainSensorData.PERIOD])
            got_amount = got_sensor_data[0].get_sensor_value([RainSensorData.RAIN, RainSensorData.PERIOD])
            self.assertEqual(other_amount, got_amount)
            self.assertEqual(other_sensor_data.get_time(), got_sensor_data[0].get_time())

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
