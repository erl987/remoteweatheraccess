"""Handles the storage of information of the weather station.

Functions:
read:               Reads the storage file.
write:              Writes the storage file.
"""
import pickle


def write(station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval):
    """Writes the data of the weather station.

    Args:
    station_data_file_name: The filename of the weather station file (relative to the current path).
    rain_calib_factor:      Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    station_name:           ID of the station (typically three letters, for example ERL).
    station_height:         Altitude of the station (in meters).
    storage_interval:       Interval of data storage at the station (in minutes).

    Returns:
    None

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( station_data_file_name, 'wb' ) as f:
        pickle.dump( dict( rain_calib_factor = rain_calib_factor, station_name = station_name, station_height = station_height, storage_interval = storage_interval ), f )


def read(station_data_file_name):
    """Returns the data of the weather station.

    Args:
    station_data_file_name: The filename of the weather station file (relative to the current path).

    Returns:
    rain_calib_factor:      Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    station_name:           ID of the station (typically three letters, for example ERL).
    station_height:         Altitude of the station (in meters).
    storage_interval:       Interval of data storage at the station (in minutes).

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( station_data_file_name, 'rb') as f:
        data = pickle.load( f );
        rain_calib_factor = data['rain_calib_factor']
        station_name = data['station_name']
        station_height = data['station_height']             # in m
        storage_interval = data['storage_interval']         # in min

        return rain_calib_factor, station_name, station_height, storage_interval