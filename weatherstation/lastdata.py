"""Handles the storage of information on the last processed weather dataset.

Functions:
read:                       Reads the storage file.
write:                      Writes the storage file.
"""
import pickle


def read(settings_file_name):
    """Returns the time and the relevant data of the last processed dataset.

    Args:
    settings_file_name:     The filename of the settings file (relative to the current path).

    Returns:
    last_old_time:          Datetime object containing the time in the last dataset stored (as Central 
                            European Time considering daylight saving).
    last_old_rain_counter:  Rain counter in that last dataset (in mm, integer format).

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( settings_file_name, 'rb') as f:
        data = pickle.load( f )
        last_old_time = data[ 'last_old_time' ]  
        last_old_rain_counter = data[ 'last_old_rain_counter' ]     # in mm

    return last_old_time, last_old_rain_counter


def write(settings_file_name, last_old_time, last_old_rain_counter):
    """Writes the time and the relevant data of the last processed dataset.

    Args:
    settings_file_name:     The filename of the settings file (relative to the current path).
    last_old_time:          Datetime object containing the time in the last dataset to be 
                            stored (as Central European Time considering daylight saving).
    last_old_rain_counter:  Rain counter in that last dataset to be stored (in mm, integer format).

    Returns:
    None

    Raises:
    IOError:                An error occured accessing the file.
    """
    with open( settings_file_name, 'wb') as f:
        pickle.dump( dict( last_old_rain_counter = last_old_rain_counter, last_old_time = last_old_time ), f )
