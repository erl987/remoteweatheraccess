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


"""Provides unit tests for the graph drawing module.

Unit tests:
test_plot_of_last_n_days:		Test for the plotting of the graph for the last n days.

Global variables:
graph_file_name:                Name of the graph file to be stored.
"""
import unittest

from weathernetwork.server import graphs
from datetime import datetime
from weathernetwork.common.datastructures import CombiSensorData, BaseStationSensorData, RainSensorData

graph_file_name = 'graph.svg'
graph_directory = './data'
sensors_to_plot = [(BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE),
                   (RainSensorData.RAIN, RainSensorData.CUMULATED),
                   ('OUT1', CombiSensorData.TEMPERATURE),
                   ('OUT1', CombiSensorData.HUMIDITY)]


class TestGraphGeneration(unittest.TestCase):
    def setUp(self):
        """Sets up each unit test."""
        self._db_file_name = "data/weather.db"
        self._station_ID = "TES2"

    def test_plot_of_last_n_days(self):
        graphs.plot_of_last_n_days(7, self._db_file_name, self._station_ID, sensors_to_plot,
                                   graph_directory, graph_file_name, True, datetime(year=2015, month=3, day=3))

    def tearDown(self):
        """Finishes each unit test."""

if __name__ == '__main__':
    unittest.main()
