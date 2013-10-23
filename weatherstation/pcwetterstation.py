"""Provides functions for managing weather data compatible to the software PC-Wetterstation.

Functions:
write:                          Writes a weather data CSV-file compatible to PC-Wetterstation for arbitrary data.
writesinglemonth:               writes a weather data CSV-file compatible to PC-Wetterstation for a single month.
convertTo:                      Converts weather data into units and format compatible to PC-Wetterstation.
"""
import csv
import os
from datetime import datetime as dt
from collections import OrderedDict

import constants
import utilities



def write( data_folder, rain_calib_factor, last_old_rain_counter, station_name, station_height, station_type, export_data, sensor_list ):
    """Writes a CSV-file with the weather data compatible to PC-Wetterstation for arbitrary data.
    
    Args:
    data_folder:                Folder where the CSV-file for PC-Wetterstation will be stored. It must be given relative to the current path.
                                The file names will be automatically "EXP_MM_YY.CSV" with MM and YY being the months and the years of the datasets.
    rain_calib_factor:          Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    last_old_rain_counter:      Last rain counter setting before the first dataset of this file (in mm).
    station_name:               ID of the station (typically three letters, for example ERL).
    station_height:             Altitude of the station (in meters).
    station_type:               Information string on the detailed type of the weather station (producer, ...).
    export_data:                Data to be written on file. It is not required to be sorted regarding time.
                                The required format is a list of ordered dicts with the key being registered in sensor_list. It must contain at least 
                                the following information in this order:
                                    - date of the data in the format dd.mm.yyyy
                                    - time of the data (local time) in the format mm:hh
                                    - all measured data according to PC-Wetterstation specification with:
                                            * wind speeds in km/h
                                            * rain in mm since last recording
                                            * temperatures in degree Celsius
                                            * pressure in hPa
                                            * humidities in percent
                                
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.

    Returns:
    None

    Raises:
    IOError:                    An error occurred accessing the file.
    """
    getmonth = lambda x: dt.strptime( x['date'], '%d.%m.%Y' )
    
    # determine the months existing in the data
    export_data = sorted( export_data, key = lambda k: dt.strptime( k['date'] + ' ' + k['time'], '%d.%m.%Y %H:%M') )
    months_set = { ( getmonth(x).month, getmonth(x).year ) for x in export_data }
    
    # write the data separately for each month into a file
    for curr_month in months_set:
        monthly_export_data = [ x for x in export_data if ( getmonth(x).month == curr_month[0] and getmonth(x).year == curr_month[1] ) ]
        writesinglemonth( data_folder, rain_calib_factor, last_old_rain_counter, station_name, station_height, station_type, monthly_export_data, sensor_list )


def writesinglemonth( data_folder, rain_calib_factor, last_old_rain_counter, station_name, station_height, station_type, export_data, sensor_list ):
    """Writes a CSV-file with the weather data compatible to PC-Wetterstation for a certain single month.
    
    Args:
    data_folder:                Folder where the CSV-file for PC-Wetterstation will be stored. It must be given relative to the current path.
                                The file name will be automatically "EXP_MM_YY.CSV" with MM and YY being the month and the year of the datasets.
    rain_calib_factor:          Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    last_old_rain_counter:      Last rain counter setting before the first dataset of this file (in mm).
    station_name:               ID of the station (typically three letters, for example ERL).
    station_height:             Altitude of the station (in meters).
    station_type:               Information string on the detailed type of the weather station (producer, ...).
    export_data:                Data to be written on file. It must be only from one single month. It is not required to be sorted regarding time.
                                The required format is a list of ordered dicts with the key being registered in sensor_list. It must contain at least 
                                the following information in this order:
                                    - date of the data in the format dd.mm.yyyy
                                    - time of the data (local time) in the format mm:hh
                                    - all measured data according to PC-Wetterstation specification with:
                                            * wind speeds in km/h
                                            * rain in mm since last recording
                                            * temperatures in degree Celsius
                                            * pressure in hPa
                                            * humidities in percent
                                
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.

    Returns:
    None

    Raises:
    IOError:                    An error occurred accessing the file.
    AssertionError:             The data in 'export_data' is from more than one month.
    """
    # Sort data
    export_data = sorted( export_data, key = lambda k: dt.strptime( k['date'] + ' ' + k['time'], '%d.%m.%Y %H:%M') )

    # Check if data is really only from one month
    getmonth = lambda x: dt.strptime( x['date'], '%d.%m.%Y' )
    months_set = { ( getmonth(x).month, getmonth(x).year ) for x in export_data }
    if len( months_set ) > 1:
        raise AssertionError( 'The data is from more than one month.' )

    # Generate file name assuming that all datasets are from one month
    firstDate = dt.strptime( export_data[0]['date'], '%d.%m.%Y')
    data_file_name = data_folder + '/EXP' + firstDate.strftime('%m_%y') + '.csv'

    # Generate settings line for the CSV-file
    settings_line = '#Calibrate=' + str( '%1.3f' % rain_calib_factor ) + ' #Regen0=' + str( int( last_old_rain_counter ) ) + 'mm #Location=' + str( station_name ) + '/' + str( int( station_height ) ) + 'm #Station=' + station_type

    # Write header lines in a PC-Wetterstation compatible CSV-file
    with open( data_file_name, 'w', newline = '\r\n', encoding='latin-1' ) as f:
        for index, key in enumerate( export_data[0] ):
            if index > 0:
                f.write(',')
            f.write( sensor_list[key][constants.name] )
        f.write( '\n' )
        for index, key in enumerate( export_data[0] ):
            if index > 0:
                f.write( ',' )
            f.write( sensor_list[key][constants.unit] )
        f.write( '\n' )
        f.write( settings_line + '\n' )

    # Store all valid data in a PC-Wetterstation compatible CSV-file
    with open( data_file_name, 'a', newline='', encoding='latin-1' ) as f:
        writer = csv.writer( f, lineterminator="\r\n" )    

        # Write sensor indices line
        sensor_index_list = [ sensor_list[key][constants.export_index] for key in export_data[0] ]
        writer.writerows( [ sensor_index_list ] );

        # Write data
        for line in export_data:
            data_output_line = [ line[key] for key in line ]
            writer.writerows( [ data_output_line ] )


def convertTo(read_data, last_old_rain_counter, sensor_list):
    """Converts weather data to units and format compatible to PC-Wetterstation.
    
    Args:
    read_data:                  List containing the new read data to be processed. For each time a list containing the data with the 
                                indices specified in 'sensor_list' must be present. It is not required to be sorted. 
                                The units of the data must be as follows:
                                    * time of measurement as standard c-time in seconds since epoch (CET considering daylight saving)
                                    * wind speeds in m/s
                                    * rain as absolute rain counter since the last reset at the measurement time (in mm)
                                    * temperatures in degree Celsius
                                    * pressure in hPa
                                    * humidities in percent
                                Invalid data is specified as 'i'.
    last_old_rain_counter:      Last rain counter setting before the first dataset of the new read data (in mm).
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in 'read_data'.
                                The keys must be identical to that used in the 'export_data'.
    
    Returns:
    export_data:                List containing the weather data compatible to PC-Wetterstation. The format is a list of ordered dicts 
                                with the key being registered in sensor_list. It contains at least the following information in this order 
                                and is sorted according to date and time:
                                    - date of the data in the format dd.mm.yyyy
                                    - time of the data (CET time considering daylight saving) in the format mm:hh
                                    - all measured data according to PC-Wetterstation specification with:
                                            * wind speeds in km/h
                                            * rain in mm since last recording
                                            * temperatures in degree Celsius
                                            * pressure in hPa
                                            * humidities in percent
                                Not measured data is given as zero.
    last_dataset_time:          Time of the last measurement in the dataset (with an accuracy of minutes).
    last_dataset_rain_counter:  Rain counter setting of the last read dataset (in mm).

    Raises:
    None
    """
     # Generate export data collection
    export_data = []
    for imported_line in read_data:
        new_line = []
        for key in sensor_list:
            if ( sensor_list[ key ][ constants.import_index ] != 'none' ):
                new_line.append( ( key, imported_line[ sensor_list[ key ][ constants.import_index ] ] ) )
            else:
                new_line.append( ( key, '0' ) )
        export_data.append( OrderedDict( new_line ) )

    # Replace non-valid values by zeros
    for line_index, line in enumerate( export_data[:] ):
        processed_line = OrderedDict( ( index, val ) if utilities.isFloat(val) else ( index, '0' ) for index, val in line.items() )
        export_data[ line_index ] = processed_line

    # Delete all sensor data that should not be exported to the CSV-file
    delete_keys = [ key for key in sensor_list if sensor_list[ key ][ constants.export_index ] == 'none' ]
    export_data = [ OrderedDict( ( key, line[key] ) for key in line if key not in delete_keys ) for line in export_data ]

    # Convert date stamps (date zone and DST according to system settings)
    for line in export_data[:]:
        curr_time = dt.fromtimestamp( int( line['date'] ) );            # import ctime seconds since epoch
        line['date'] = curr_time.strftime( '%d.%m.%Y' )
        line['time'] = curr_time.strftime( '%H:%M' )

    # Sort data
    export_data = sorted( export_data, key = lambda k: dt.strptime( k['date'] + ' ' + k['time'], '%d.%m.%Y %H:%M') )

    # Perform required unit convertions
    for line in export_data[:]:
        line['windGusts'] = str( float( line['windGusts'] ) * 3.6 );    # convert from m/s to km/h
        line['windSpeed'] = str( float( line['windSpeed'] ) * 3.6 );    # convert from m/s to km/h
        line['windDir'] = str( float( line['windDir'] ) * 22.5 );       # convert to degree

    # Calculate rain amount differences
    rain_counters = [ float( line['rainCounter'] ) for line in export_data ]
    rain_counters.insert( 0, last_old_rain_counter )
    rain_amounts = [ x - rain_counters[i-1] for i, x in enumerate( rain_counters ) ][1:]
    for export_line, amount in zip( export_data[:], rain_amounts ):
        export_line['rainCounter'] = str( amount );                      # set to rain amount differences since the last dataset before the current (in mm)

    last_dataset_time = dt.strptime( export_data[-1]['date'] + ' ' + export_data[-1]['time'], '%d.%m.%Y %H:%M') # the accuracy is minutes
    last_dataset_rain_counter = rain_counters.pop()
    return export_data, last_dataset_time, last_dataset_rain_counter