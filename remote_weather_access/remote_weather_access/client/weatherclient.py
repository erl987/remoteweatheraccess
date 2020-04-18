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


"""Read in data from a TE923-compatible weather station via USB and store the data in a CSV-file compatible to
PC-Wetterstation.
"""
import sys

from ..client import te923ToCSVreader

data_folder = '/opt/weatherstation/configData/'
station_data_file_name = 'stationData.dat'

input_list = sys.argv
script_name = input_list.pop(0)

# Read new weather data from the TE923-station and save it in a CSV-file compatible to PC-Wetterstation
te923ToCSVreader.te923ToCSVreader(data_folder, station_data_file_name, script_name)
