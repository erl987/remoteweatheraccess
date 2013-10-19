"""Management of TE923-weather station data transfer.

Functions:
readdata:                   Read all new data from the weatherstation.
"""

def readdata():
    """Reads all new data from the weatherstation

    Args:
    None

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
                                - rain counter                  [mm since last resetting]
                            Invalid data members are marked with 'i'


    Raises:
    None
    """

    data_sets_list = ['1381578982:21.75:51:7.30:92:i:i:i:i:i:i:i:i:1016.4:3.4:5:0:13:15.2:23.2:5.2:920',
                 '1381578920:22.34:59:8.30:91:i:i:i:i:i:i:i:i:1014.4:2.1:5:0:1:7.8:20.9:23.4:900',
                '1380577982:21.32:62:6.30:95:i:i:i:i:i:i:i:i:1012.4:6.4:5:0:15:43.5:3.4:2.1:882']

    data = list()
    for curr_data_set in data_sets_list:
        data.append( str.split( curr_data_set, ":" ) )

    return data