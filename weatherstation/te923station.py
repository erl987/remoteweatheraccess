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


"""Management of TE923-weather station data transfer.

Functions:
readdata:                       Read all new data from the weatherstation.

Constants:
weather_station_reader_path:    Path to the weather station reader tool.
"""
import os

# the weatherstation reader tool must be called using root privileges
weather_station_reader_path = 'sudo /opt/weatherstation/te923tool-0.6.1/te923con'


def readdata(is_read_all_datasets):
    """Reads all new data from the weatherstation

    Args:
    is_read_all_datasets:   Flag stating if only the latest (False) or all datasets should be read from the weatherstation (True)

    Returns:
    data:                   List containing the new data read from the station for each timepoint separately.
                            Format of the list members in the following order (see also http://te923.fukz.org/documentation.html):
                                - time                          [C-time, seconds since epoch]
                                - inside temperature            [deg C]
                                - inside humidity               [%]
                                - outside temperature 1         [deg C]
                                - outside humidity 1            [%]
                                - outside temperature 2         [deg C]
                                - outside humidity 2            [%]
                                - outside temperature 3         [deg C]
                                - outside humidity 3            [%]
                                - outside temperature 4         [deg C]
                                - outside humidity 4            [%]
                                - outside temperature 5         [deg C]
                                - outside humidity 5            [%]
                                - air pressure                  [hPa]
                                - UV-index                      [-]
                                - weather forecast              [0 - heavy snow
                                                                1 - little snow
                                                                2 - heavy rain
                                                                3 - little rain
                                                                4 - cloudy
                                                                5 - some clouds
                                                                6 - sunny]
                                - storm warning                 [ 0 - no warning, 1 - warning]
                                - wind direction                [n x 22.5 deg, 0 -> north]
                                - average wind speed            [m/s]
                                - wind gusts                    [m/s]
                                - temperature of wind sensor    [deg C]
                                - rain counter                  [tipping bucket counts since last resetting]
                            Invalid data members are marked with 'i'


    Raises:
    EnvironmentError:       No connection to the weather station was possible.
    """
    # Call the C-program for reading the data from the weather station
    output_stream = []
    if is_read_all_datasets:
        output_stream = os.popen( weather_station_reader_path + ' -b' )
    else:
        output_stream = os.popen( weather_station_reader_path )

    # check for reading errors
    if not output_stream:
        raise EnvironmentError( 'No connection to the weather station was possible.' )

    # Reformat the output data
    data_sets_list = [ line.strip() for line in output_stream ]
    data = [ str.split( line, ":" ) for line in data_sets_list ]

    return data