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
data_folder:                    Path to the test data folder.
graph_file_name:                Name of the graph file to be stored.
"""
import unittest

import graphs

data_folder = './data'
graph_file_name = 'graph.svg'


class Test_graphs(unittest.TestCase):
    def setUp(self):
        '''Sets up each unit test.'''


    def test_plot_of_last_n_days(self):
        sensors_to_plot = [ 'pressure', 'rainCounter', 'tempOutside1', 'humidOutside1' ]
        graphs.plot_of_last_n_days( 7, data_folder, sensors_to_plot, data_folder, graph_file_name, False )     


    def tearDown(self):
        '''Finishes each unit test.'''

if __name__ == '__main__':
    unittest.main()






