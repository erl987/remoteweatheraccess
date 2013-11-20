"""Provides unit tests for the module te923ToCSVreader.

Unit tests:
test_first_execution:           Tests the behviour in case of first execution with no last data file being present.
test_single_data_read:          Test the behaviour if one new dataset has been read (i.e. a call between [1.0 ... 2.0[ * storage_interval).
test_no_new_data_read:          Test the behaviour if no new dataset has been read (i.e. a call between [0.0 ... 1.0[ * storage_interval).
test_multiple_data_read:        Test the behaviour if multiple new datasets have been read (i.e. a call > 1.0 * storage_interval).
distant_data_read:              Test the behaviour if datasets with time gaps in between are read (this requires special handling of rain counters).

Global variables:
data_folder:                    Temporary folder containing the test data. It will be deleted after the tests.
station_data_file_name:         Name of the station data file in the test data folder.
rain_calib_factor:              Rain calibration factor of the test station. Dummy value.
station_name:                   Name of the test weather station. Dummy value.
station_height:                 Height of the test weather station (in meters). Dummy value
storage_interval:               Storage interval of the test weather station (in minutes)
ftp_passwd:                     Password for the FTP-server
ftp_server:                     Name of the FTP-server where the data is transfered to
ftp_folder:                     Directory on the FTP-server where the data is stored
settings_file_name:             Name of the settings file name in the test data folder
"""
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from datetime import datetime as dt
from datetime import timedelta
import os
import shutil
import logging

import te923ToCSVreader
import stationdata
import lastdata
import te923station

data_folder = './test_data/'
station_data_file_name = 'stationData.dat'
rain_calib_factor = 1.0
station_name = 'TES'
station_height = 100.0
storage_interval = 10.0
ftp_passwd = 'weatherstation#10'
ftp_server = 'h1864277.stratoserver.net' 
ftp_folder = 'newData'
settings_file_name = 'settings_TES.dat' # TODO: no ideal solution!!!!!!


class SpoofDate(dt):
    '''Class for mocking parts of the datetime object in the tested module.'''
    def __new__(cls, *args, **kwargs):
        return dt.__new__(dt, *args, **kwargs)


class TestProcessToCSV(unittest.TestCase):
    def setUp(self):
        '''Sets up each unit test.'''
        # Generate test folder
        os.makedirs( data_folder, exist_ok = True )

        # Generate station data file
        stationdata.write( data_folder + station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, ftp_folder )


    @patch('te923ToCSVreader.dt', SpoofDate)
    def test_first_execution(self):
        '''Tests the behviour in case of first execution with no last data file being present.'''
        # Simulate reading of weather data
        time_last = 1382374260 - storage_interval * 60 # in seconds since epoch (CET including possible daylight saving) '21.10.2013,18:51
        te923station.readdata = Mock( return_value = 
                                            [ [ str( int( time_last + 1 * storage_interval * 60 ) ), '30.00', '63', '14.50','87', 'i','i','i','i','i','i','i','i', '1017.1', 'i', 0, 0, 'i','i', 'i', 'i', 906 ],
                                              [ str( int( time_last + 2 * storage_interval * 60 ) ), '15.00', '63', '14.50','87', 'i','i','i','i','i','i','i','i', '1017.1', 'i', 0, 0, 'i','i', 'i', 'i', 906 ],
                                              [ str( int( time_last + 3 * storage_interval * 60 ) ), '10.00', '63', '14.50','87', 'i','i','i','i','i','i','i','i', '1017.1', 'i', 0, 0, 'i','i', 'i', 'i', 906 ] ] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last ) + 3.2 * timedelta( minutes = storage_interval ) )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        # TODO: implement useful assert


    @patch('te923ToCSVreader.dt', SpoofDate)
    def test_single_data_read(self):
        '''Test the behaviour if one new dataset has been read (i.e. a call between [1.0 ... 2.0[ * storage_interval).'''
        time_last = 1381578982 # in seconds since epoch (CET including possible daylight saving)      
         
        # Generate last data file consistent to the test case
        lastdata.write( data_folder + settings_file_name, dt.fromtimestamp( time_last ), 880 )

        # Simulate reading of weather data
        te923station.readdata = Mock( return_value = [ [ str( int( time_last + 1 * storage_interval * 60 ) ), '21.75', '51', '7.30', '92', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1016.4', '3.4', '5', '0', '13', '15.2', '23.2', '5.2', '882' ] ] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last) + 1.2 * timedelta( minutes = storage_interval ) )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        # TODO: implement useful assert


    @patch('te923ToCSVreader.dt', SpoofDate)
    def test_no_new_data_read(self):
        '''Test the behaviour if no new dataset has been read (i.e. a call between [0.0 ... 1.0[ * storage_interval).'''
        time_last = 1381578982 # in seconds since epoch (CET including possible daylight saving)   
        set_last_old_rain_counter = 880   
         
        # Generate last data file consistent to the test case
        lastdata.write( data_folder + settings_file_name, dt.fromtimestamp( time_last ), set_last_old_rain_counter )

        # Simulate reading of weather data
        te923station.readdata = Mock( return_value = [] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last ) + 0.8 * timedelta( minutes = storage_interval ) )
        with self.assertRaises(SystemExit):
            te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        
        # Check if the last stored dataset remained unchanged
        is_reading, read_last_old_time, read_last_old_rain_counter = lastdata.read( data_folder + settings_file_name )
        self.assertEqual( read_last_old_time, dt.fromtimestamp( time_last ) )
        self.assertEqual( read_last_old_rain_counter, set_last_old_rain_counter )
        self.assertFalse( is_reading )


    @patch('te923ToCSVreader.dt', SpoofDate)
    def test_multiple_data_read(self):
        '''Test the behaviour if multiple new datasets have been read (i.e. a call > 1.0 * storage_interval).'''
        time_last = 1381578982 # in seconds since epoch (CET including possible daylight saving)      
         
        # Generate last data file consistent to the test case
        lastdata.write( data_folder + settings_file_name, dt.fromtimestamp( time_last ), 880 )

        # Simulate reading of weather data
        te923station.readdata = Mock( return_value = 
                                          [ [ str( int( time_last + 1 * storage_interval * 60 ) ), '21.75', '51', '7.30', '92', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1016.4', '3.4', '5', '0', '13', '15.2', '23.2', '5.2', '882' ],
                                            [ str( int( time_last + 2 * storage_interval * 60 ) ), '22.34',' 59', '8.30', '91', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1014.4', '2.1', '5', '0', '1', '7.8', '20.9', '23.4', '900' ],
                                            [ str( int( time_last + 3 * storage_interval * 60 ) ), '21.32', '62', '6.30', '95', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1012.4', '6.4', '5', '0', '15', '43.5', '3.4', '2.1', '920'] ] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last ) + 3.8 * timedelta( minutes = storage_interval ) )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        # TODO: implement useful assert


    @patch('te923ToCSVreader.dt', SpoofDate)
    def test_distant_data_read(self):
        '''Test the behaviour if datasets with time gaps in between are read (this requires special handling of rain counters).'''
        time_last = 1381578982 # in seconds since epoch (CET including possible daylight saving)      
         
        # Generate last data file consistent to the test case
        lastdata.write( data_folder + settings_file_name, dt.fromtimestamp( time_last ), 880 )

        # Simulate reading of weather data
        te923station.readdata = Mock( return_value = 
                                          [ [ str( int( time_last + 2 * storage_interval * 60 ) ), '21.75', '51', '7.30', '92', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1016.4', '3.4', '5', '0', '13', '15.2', '23.2', '5.2', '882' ],
                                            [ str( int( time_last + 3 * storage_interval * 60 ) ), '22.34',' 59', '8.30', '91', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1014.4', '2.1', '5', '0', '1', '7.8', '20.9', '23.4', '886' ],
                                            [ str( int( time_last + 4 * storage_interval * 60 ) ), '21.32', '62', '6.30', '95', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1012.4', '6.4', '5', '0', '15', '43.5', '3.4', '2.1', '887'] ] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last ) + 4.2 * timedelta( minutes = storage_interval ) )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        # TODO: implement useful assert


    @patch('te923ToCSVreader.dt', SpoofDate)
    @patch('server.dt', SpoofDate)
    def test_two_months_read(self):
        '''Test the behaviour in case of a month change during the reading.'''
        time_last = 1383259782 # in seconds since epoch (CET including possible daylight saving)      
         
        # Generate last data file consistent to the test case
        lastdata.write( data_folder + settings_file_name, dt.fromtimestamp( time_last ), 880 )

        # Simulate reading of weather data
        te923station.readdata = Mock( return_value = 
                                          [ [ str( int( time_last + 1 * storage_interval * 60 ) ), '21.75', '51', '7.30', '92', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1016.4', '3.4', '5', '0', '13', '15.2', '23.2', '5.2', '882' ],
                                            [ str( int( time_last + 2 * storage_interval * 60 ) ), '22.34',' 59', '8.30', '91', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1014.4', '2.1', '5', '0', '1', '7.8', '20.9', '23.4', '886' ],
                                            [ str( int( time_last + 3 * storage_interval * 60 ) ), '21.32', '62', '6.30', '95', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1012.4', '6.4', '5', '0', '15', '43.5', '3.4', '2.1', '887'] ] )
        SpoofDate.now = classmethod( lambda cls : dt.fromtimestamp( time_last ) + 3.2 * timedelta( minutes = storage_interval ) )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name, 'testScript' )
        # TODO: implement useful assert


    def tearDown(self):
        '''Finishes each unit test.'''
        # Remove test folder and all test files
        shutil.rmtree( data_folder )


if __name__ == '__main__':
    unittest.main()
