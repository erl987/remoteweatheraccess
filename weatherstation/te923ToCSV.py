"""Read in data from a TE923-compatible weather station via USB and store the data in a CSV-file compatible to PC-Wetterstation."""
import datetime
from collections import OrderedDict

import constants
import stationdata
import lastdata
import te923station
import pcwetterstation

data_folder = './data/'
station_data_file_name = 'stationData.dat'

station_type = 'TE923/924 (Mebus,Irox,Honeywell,Cresta)'
# Containing the list of all sensors read from the weather station and their mapping to the PC-Wetterstation format
# The tuples contain: ( index in import data, description of sensor, index in PC-Wetterstation software, data unit required by PC-Wetterstation )
# Irrelevant sensors indices are marked by 'none'
sensor_list = OrderedDict( [
    ('date',           (0,        'Datum',                                            '',     ''                  )),
    ('time',           ('none',   'Zeit',                                             '',     ''                  )),
    ('tempInside',     (1,        'Temp. I.',                                          1,     '\N{DEGREE SIGN}C'  )),
    ('humidInside',    (2,        'Feuchte I.',                                       17,     '%'                 )),
    ('tempOutside1',   (3,        'Temp. A. 1',                                        2,     '\N{DEGREE SIGN}C'  )),
    ('humidOutside1',  (4,        'Feuchte A. 1',                                     18,     '%'                 )),
    ('tempOutside2',   (5,        'Temp. A. 2',                                        3,     '\N{DEGREE SIGN}C'  )),
    ('humidOutside2',  (6,        'Feuchte A. 2',                                     19,     '%'                 )),
    ('tempOutside3',   (7,        'Temp. A. 3',                                        4,     '\N{DEGREE SIGN}C'  )),
    ('humidOutside3',  (8,        'Feuchte A. 3',                                     20,     '%'                 )),
    ('tempOutside4',   (9,        'Temp. A. 4',                                        5,     '\N{DEGREE SIGN}C'  )),
    ('humidOutside4',  (10,       'Feuchte A. 4',                                     21,     '%'                 )),
    ('tempOutside5',   (11,       'Temp. A. 5',                                        6,     '\N{DEGREE SIGN}C'  )),
    ('humidOutside5',  (12,       'Feuchte A. 5',                                     22,     '%'                 )),
    ('pressure',       (13,       'Luftdruck',                                       133,     'hPa'               )),
    ('UV',             (14,       'UV-X',                                              9,     'UV-I'              )),
    ('forecast',       (15,       'Vorhersage',                                   'none',     ''                  )),
    ('warning',        (16,       'Sturmwarnung',                                 'none',     ''                  )),
    ('windDir',        (17,       'Richtung',                                         36,     '\N{DEGREE SIGN}'   )),
    ('windSpeed',      (18,       'Wind',                                             35,     'km/h'              )),
    ('windGusts',      (19,       'Windb\N{LATIN SMALL LETTER O WITH DIAERESIS}en',   45,     'km/h'              )),
    ('tempWind',       (20,       'Temp. Wind',                                        8,     '\N{DEGREE SIGN}C'  )),
    ('rainCounter',    (21,       'Regen',                                            34,     'mm'                ))
    ] )


# Read station data
rain_calib_factor, station_name, station_height, storage_interval = stationdata.read( data_folder + station_data_file_name )
settings_file_name = 'settings_' + station_name + '.dat'
imported_data = te923station.readdata()

# Get data for the earliest new reading
firstNewDataIndex = 0
firstNewRainCounter = float( imported_data[ firstNewDataIndex ][ sensor_list[ 'rainCounter' ][ constants.import_index ] ] )
firstNewTime = datetime.datetime.fromtimestamp( int( imported_data[ firstNewDataIndex ] [ sensor_list[ 'date' ][ constants.import_index ] ] ) )

# Read settings file
try:
    lastOldTime, last_old_rain_counter = lastdata.read( data_folder + settings_file_name )
except Exception:
    # If this is first date the program is executed the only choice is to start with the data from the earliest new reading
    lastOldTime = firstNewTime
    last_old_rain_counter = firstNewRainCounter

# Ensure that the last rain counter value is not too old and valid
if ( firstNewTime - lastOldTime ) > datetime.timedelta( minutes = storage_interval ) or ( lastOldTime >= firstNewTime ):
    last_old_rain_counter = firstNewRainCounter
if last_old_rain_counter > firstNewRainCounter:
    last_old_rain_counter = firstNewRainCounter

# Write weather data to PC-Wetterstation CSV-file
export_data, last_dataset_time, last_dataset_rain_counter = pcwetterstation.convertTo( imported_data, last_old_rain_counter, sensor_list )
pcwetterstation.write( data_folder, rain_calib_factor, last_old_rain_counter, station_name, station_height, station_type, export_data, sensor_list )

# Refresh settings file
lastdata.write( data_folder + settings_file_name, last_dataset_time, last_dataset_rain_counter )
