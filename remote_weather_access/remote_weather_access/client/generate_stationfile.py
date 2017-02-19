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

"""Generates a file for the station data.

Constants:
station_data_file_name:         Name of the station data file in the test data folder.
rain_calib_factor:              Rain calibration factor of the test station. Dummy value.
station_name:                   Name of the test weather station. Dummy value.
station_height:                 Height of the test weather station (in meters). Dummy value
storage_interval:               Storage interval of the test weather station (in minutes)
ftp_passwd:                     Password for the FTP-server
ftp_server:                     Name of the FTP-server where the data is transfered to
port:                           Connection port of the FTP-server (default: port 21)
ftp_folder:                     Directory on the FTP-server where the data is stored
"""
from client import stationdata

station_data_file_name = 'stationData.dat'
rain_calib_factor = 1.0
station_name = 'station'
station_height = 290.0
storage_interval = 10.0
ftp_passwd = 'password'
ftp_server = 'server.com' 
port = 9999
ftp_folder = 'newData'

stationdata.write( station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, port, ftp_folder )