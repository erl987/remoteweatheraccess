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


"""Handles the storage of information on the last processed weather dataset.

Functions:
read:                       Reads the storage file.
set_reading:                Reset the station reading flag.
write:                      Writes the storage file.
"""
import pickle
import datetime
from datetime import datetime as dt


def read(settings_file_name):
    """Returns the time and the relevant data of the last processed dataset.

    Args:
    settings_file_name:     The filename of the settings file (relative to the current path).

    Returns:
    is_reading:             Flag stating if it is currently read from the weatherstation (true) or not (false)
    last_old_time:          Datetime object containing the time in the last dataset stored (as Central 
                            European Time considering daylight saving).
    last_old_rain_counter:  Rain counter in that last dataset (in tipping bucket counts, integer format).

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( settings_file_name, 'rb') as f:
        data = pickle.load( f )
        last_old_time = data[ 'last_old_time' ]  
        last_old_rain_counter = data[ 'last_old_rain_counter' ]     # in tipping bucket counts
        is_reading = data[ 'is_reading' ]

    return is_reading, last_old_time, last_old_rain_counter


def set_reading(settings_file_name, new_is_reading):
    """Reset the station reading flag. If the file is not existing, it is created. All other values are then invalid.

    Args:
    settings_file_name:     The filename of the settings file (relative to the current path).
    is_reading:             Flag stating if it is currently read from the weatherstation (true) or not (false)    

    Returns:
    None

    Raises:
    IOError:                An error occured accessing the file.
    """
    try:
        old_is_reading, last_old_time, last_old_rain_counter = read( settings_file_name )
    except Exception:
        # If the file is not yet existing, this data will be invalid
        last_old_time = dt( year = datetime.MINYEAR, month = 1, day = 1 )
        last_old_rain_counter = -1000000

    # Rewrite all data unchanged to the file except of the reading flag
    with open( settings_file_name, 'wb') as f:
        pickle.dump( dict( last_old_rain_counter = last_old_rain_counter, last_old_time = last_old_time, is_reading = new_is_reading ), f )


def write(settings_file_name, last_old_time, last_old_rain_counter):
    """Writes the time and the relevant data of the last processed dataset. The reading flag is set to false by default.

    Args:
    settings_file_name:     The filename of the settings file (relative to the current path).
    last_old_time:          Datetime object containing the time in the last dataset to be 
                            stored (as Central European Time considering daylight saving).
    last_old_rain_counter:  Rain counter in that last dataset to be stored (in tipping bucket counts, integer format).

    Returns:
    None

    Raises:
    IOError:                An error occured accessing the file.
    """
    with open( settings_file_name, 'wb') as f:
        pickle.dump( dict( last_old_rain_counter = last_old_rain_counter, last_old_time = last_old_time, is_reading = False ), f )
