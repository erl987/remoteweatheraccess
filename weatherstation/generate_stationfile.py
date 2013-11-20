"""Generates a file for the station data.

Constants:
station_data_file_name:         Name of the station data file in the test data folder.
rain_calib_factor:              Rain calibration factor of the test station. Dummy value.
station_name:                   Name of the test weather station. Dummy value.
station_height:                 Height of the test weather station (in meters). Dummy value
storage_interval:               Storage interval of the test weather station (in minutes)
ftp_passwd:                     Password for the FTP-server
ftp_server:                     Name of the FTP-server where the data is transfered to
ftp_folder:                     Directory on the FTP-server where the data is stored
"""
import stationdata

station_data_file_name = 'stationData.dat'
rain_calib_factor = 1.0
station_name = 'ERL'
station_height = 290.0
storage_interval = 10.0
ftp_passwd = 'weatherstation#10'
ftp_server = 'h1864277.stratoserver.net' 
ftp_folder = 'newData'

stationdata.write( station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, ftp_folder )