"""Handles the storage of information of the weather station.

Functions:
read:               Reads the storage file.
write:              Writes the storage file.
"""
import pickle


def write(station_data_file_name, rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, port, ftp_folder):
    """Writes the data of the weather station.

    Args:
    station_data_file_name: The filename of the weather station file (relative to the current path).
    rain_calib_factor:      Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    station_name:           ID of the station (typically three letters, for example ERL).
    station_height:         Altitude of the station (in meters).
    storage_interval:       Interval of data storage at the station (in minutes).
    ftp_passwd:             Password for the FTP-server where the weather data is transferred (the user name is identical to the station name)
    ftp_server:             Address of the FTP-server where the weather data is transferred
    port:                   Connection port of the FTP-server
    ftp_folder:             Directory on the server where the data is stored

    Returns:
    None

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( station_data_file_name, 'wb' ) as f:
        pickle.dump( dict( rain_calib_factor = rain_calib_factor, station_name = station_name, station_height = station_height, 
                          storage_interval = storage_interval, ftp_passwd = ftp_passwd, ftp_server = ftp_server, port = port, ftp_folder = ftp_folder ), f )


def read(station_data_file_name):
    """Returns the data of the weather station.

    Args:
    station_data_file_name: The filename of the weather station file (relative to the current path).

    Returns:
    rain_calib_factor:      Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    station_name:           ID of the station (typically three letters, for example ERL).
    station_height:         Altitude of the station (in meters).
    storage_interval:       Interval of data storage at the station (in minutes).
    ftp_passwd:             Password for the FTP-server where the weather data is transferred (the user name is identical to the station name)
    ftp_server:             Address of the FTP-server where the weather data is transferred
    port:                   Connection port of the FTP-server
    ftp_folder:             Directory on the server where the data is stored

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( station_data_file_name, 'rb') as f:
        data = pickle.load( f );
        rain_calib_factor = data['rain_calib_factor']
        station_name = data['station_name']
        station_height = data['station_height']             # in m
        storage_interval = data['storage_interval']         # in min
        ftp_passwd = data['ftp_passwd']
        ftp_server = data['ftp_server']
        port = data['port']
        ftp_folder = data['ftp_folder']

        return rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, port, ftp_folder