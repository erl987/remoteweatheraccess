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
