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


"""Provides unit tests for the module pcwetterstation.

Unit tests:
test_read:                      Tests the reading of a PC-Wetterstation compatible CSV-file.
test_merge:                     Tests the merging of two PC-Wetterstation compatible CSV-files.

Global variables:
data_folder:                    Path to the test data folder
"""
import unittest

import pcwetterstation
import te923ToCSVreader

data_folder = '.\data'


class Test_pcwetterstation(unittest.TestCase):
    def setUp(self):
        '''Sets up each unit test.'''


    def test_read(self):
        test_file_name = 'EXP10_13.csv'

        data, key_list, rain_calib_factor, rain_counter_base, station_name, station_height, station_type, sensor_descriptions, sensor_units = pcwetterstation.read( data_folder, test_file_name, te923ToCSVreader.sensor_list )


    def test_merge(self):
        test_file_name_1 = '1_EXP10_13.csv'
        test_file_name_2 = '2_EXP10_13.csv'
        merged_files = pcwetterstation.merge( data_folder, data_folder, test_file_name_1, data_folder, test_file_name_2, te923ToCSVreader.sensor_list, True )


    def tearDown(self):
        '''Finishes each unit test.'''

if __name__ == '__main__':
    unittest.main()
