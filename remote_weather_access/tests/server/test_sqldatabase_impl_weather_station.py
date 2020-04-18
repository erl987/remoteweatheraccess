# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
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

from ..builder_acessors import *
from ...remote_weather_access.common.datastructures import WeatherStationMetadata
from ...remote_weather_access.server._sqldatabase_impl import _WeatherStationTable
from ...remote_weather_access.server.exceptions import NotExistingError, AlreadyExistingError


class Station(object):
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


def database_object():
    """Test database factory"""
    db_file_path = "./tests/workingDir/sqltest/"
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
        # given:
        weather_station_table = _WeatherStationTable(self._sql)

        # when:
        with self._sql:
            station_id = "TES"

        # then:
            self.assertRaises(NotExistingError, weather_station_table.get_metadata, station_id)

    def test_get_stations(self):
        # given:
        weather_station_table = _WeatherStationTable(self._sql)
        station_id = "TES"
        station = a(station_object().with_station_id(station_id))

        # when:
        with self._sql:
            weather_station_table.add(station)
            stations = weather_station_table.get_stations()

        # then:
        self.assertEqual(stations, [station_id])


if __name__ == '__main__':
    unittest.main()
