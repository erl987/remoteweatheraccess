# Read in data from a TE923-compatible weather station via USB and store the data in a CSV-file compatible to PC-Wetterstation
import string
import csv
import sys
import datetime
import pickle
from collections import OrderedDict

import utilities
import stationdata

data_folder = './data/'
station_data_file_name = 'stationData.dat'

import_index = 0
name = 1
export_index = 2
unit = 3

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

# Dummy data string as transferred from TE923 weather station
# Format: T0:H0:T1:H1:T2:H2:T3:H3:T4:H4:T5:H5:PRESS:UV:FC:STORM:WD:WS:WG:WC:RC
data_sets_list = ['1381578982:21.75:51:7.30:92:i:i:i:i:i:i:i:i:1016.4:3.4:5:0:13:15.2:23.2:5.2:882',
             '1381579142:22.34:59:8.30:91:i:i:i:i:i:i:i:i:1014.4:2.1:5:0:1:7.8:20.9:23.4:900',
            '1381579782:21.32:62:6.30:95:i:i:i:i:i:i:i:i:1012.4:6.4:5:0:15:43.5:3.4:2.1:920']

# Read station data
try:
    data = pickle.load( open( data_folder + station_data_file_name, 'rb' ) );
    rain_calib_factor = data['rain_calib_factor']
    station_name = data['station_name']
    station_height = data['station_height']
    storage_interval = data['storage_interval'] # in min
    settings_file_name = 'settings_' + station_name + '.dat'
except Exception:
    sys.exit('Station data file ' + station_data_file_name + ' could not be opened!')

# Read in new data from the weather station
# TODO: read from station
importedData = list()
for currDataSet in data_sets_list:
    importedData.append( str.split( currDataSet, ":" ) )

# Get data for the earliest new reading
firstNewDataIndex = 0
firstNewRainCounter = float( importedData[ firstNewDataIndex ][ sensor_list[ 'rainCounter' ][ import_index ] ] )
firstNewTime = datetime.datetime.fromtimestamp( int( importedData[ firstNewDataIndex ] [ sensor_list[ 'date' ][ import_index ] ] ) )

# Read settings file
try:
    data = pickle.load( open( data_folder + settings_file_name, 'rb' )  )
    lastOldTime = data[ 'lastOldTime' ]  
    lastOldRainCounter = data[ 'lastOldRainCounter' ]
except Exception:
    # If this is first date the program is executed the only choice is to start with the data from the earliest new reading
    lastOldTime = firstNewTime

# Ensure that the last rain counter value is not too old and valid
if ( firstNewTime - lastOldTime ) > datetime.timedelta( minutes = storage_interval ) or ( lastOldTime >= firstNewTime ):
    lastOldRainCounter = firstNewRainCounter
if lastOldRainCounter > firstNewRainCounter:
    lastOldRainCounter = firstNewRainCounter

# Generate file name # TODO: requires generalization for handling different months in one dataset
dataFileName = 'EXP' + firstNewTime.strftime('%m_%y') + '.csv'

# Generate settings line for the CSV-file
settingsLine = '#Calibrate=' + str( '%1.3f' % rain_calib_factor ) + ' #Regen0=' + str( int( lastOldRainCounter ) ) + 'mm #Location=' + str( station_name ) + '/' + str( int( station_height ) ) + 'm #Station=' + station_type

# Generate export data collection
exportData = []
for importedLine in importedData:
    exportData.append( OrderedDict( ( key, importedLine[ sensor_list[ key ][ import_index ] ] ) if sensor_list[ key ][ import_index ] != 'none' else ( key, '0' ) for key in sensor_list ) )

# Replace non-valid values by zeros
for lineIndex, line in enumerate( exportData[:] ):
    processedLine = OrderedDict( ( index, val ) if utilities.isFloat(val) else ( index, '0' ) for index, val in line.items() )
    exportData[ lineIndex ] = processedLine

# Delete all sensor data that should not be exported to the CSV-file
delete_keys = [ key for key in sensor_list if sensor_list[ key ][ export_index ] == 'none' ]
exportData = [ OrderedDict( ( key, line[key] ) for key in line if key not in delete_keys ) for line in exportData ]

# Convert date stamps (date zone and DST according to system settings)
for line in exportData[:]:
    currTime = datetime.datetime.fromtimestamp( int( line['date'] ) );
    line['date'] = currTime.strftime( '%d.%m.%Y' )
    line['time'] = currTime.strftime( '%H:%M' )

# Perform required unit convertions
for line in exportData[:]:
    line['windGusts'] = str( float( line['windGusts'] ) * 3.6 );    # convert from m/s to km/h
    line['windSpeed'] = str( float( line['windSpeed'] ) * 3.6 );    # convert from m/s to km/h
    line['windDir'] = str( float( line['windDir'] ) * 22.5 );       # convert to degree

# Calculate rain amount differences
rainCounters = [ float( line['rainCounter'] ) for line in exportData ]
rainCounters.insert( 0, lastOldRainCounter )
rainAmounts = [ x - rainCounters[i-1] for i, x in enumerate( rainCounters ) ][1:]
for exportLine, amount in zip( exportData[:], rainAmounts ):
    exportLine['rainCounter'] = str( amount );                      # replace by rain amount differences

# Write header lines in a PC-Wetterstation compatible CSV-file
# TODO: try / catch
f = open( data_folder + dataFileName, 'w' )
for index, key in enumerate( exportData[0] ):
    if index > 0:
        f.write(',')
    f.write( sensor_list[key][name] )
f.write('\n')
for index, key in enumerate( exportData[0] ):
    if index > 0:
        f.write(',')
    f.write( sensor_list[key][unit] )
f.write('\n')
f.write( settingsLine + '\n' )
f.close()

# Store all valid data in a PC-Wetterstation compatible CSV-file
with open( data_folder + dataFileName, 'a', newline='') as f:
    writer = csv.writer( f )    

    # Write sensor indices line
    sensorIndexList = [ sensor_list[key][export_index] for key in exportData[0] ]
    writer.writerows( [ sensorIndexList ] );

    # Write data
    for line in exportData:
        dataOutputLine = [ line[key] for key in line ]
        writer.writerows( [ dataOutputLine ] )

# Refresh settings file
lastOldRainCounter = rainCounters.pop()
lastOldTime = datetime.datetime.fromtimestamp( int( importedData.pop()[ sensor_list['date'][import_index] ] ) )
with open( data_folder + settings_file_name, 'wb') as f:
    pickle.dump( dict( lastOldRainCounter = lastOldRainCounter, lastOldTime = lastOldTime ), f )
