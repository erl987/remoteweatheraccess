"""Management of TE923-weather station data transfer.

Functions:
readdata:                   Read all new data from the weatherstation.
"""
import os


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
                                - rain counter                  [mm since last resetting]
                            Invalid data members are marked with 'i'


    Raises:
    EnvironmentError:       No connection to the weather station was possible.
    """
    # Call the C-program for reading the data from the weather station
    output_stream = []
    if ( is_read_all_datasets ):
        output_stream = os.popen( 'sudo te923tool-0.6.1/te923con -b' ) # TODO: is sudo here the best solution???
    else:
        ouptut_stream = os.popen( 'sudo te923tool-0.6.1/te923con' )

    # check for reading errors
    if not output_stream:
        raise EnvironmentError( 'No connection to the weather station was possible.' )

    # Reformat the output data
    data_sets_list = [ line.strip() for line in output_stream ]
    data = [ str.split( line, ":" ) for line in data_sets_list ]

    return data