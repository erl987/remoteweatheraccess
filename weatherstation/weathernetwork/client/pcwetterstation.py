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


"""Provides functions for managing weather data compatible to the software PC-Wetterstation.

Functions:
write:                          Writes a weather data CSV-file compatible to PC-Wetterstation for arbitrary data.
writesinglemonth:               writes a weather data CSV-file compatible to PC-Wetterstation for a single month.
read:                           Reads a CSV-file with the weather data compatible to PC-Wetterstation.
merge:                          Merges two CSV-files compatible to PC-Wetterstation.
convertTo:                      Converts weather data into units and format compatible to PC-Wetterstation.
finddatafiles:                  Finds all PC-Wetterstation files in a given folder.
deletedatafiles:                Deletes all given files from a given folder.
"""
import csv
import os
import datetime
from datetime import datetime as dt
from collections import OrderedDict

from weathernetwork.client import constants
from weathernetwork.common import utilities


data_file_tag = 'EXP'       # indicating a PC-Wetterstation data file


def write( data_folder, rain_calib_factor, station_name, station_height, station_type, export_data, key_list, sensor_list ):
    """Writes a CSV-file with the weather data compatible to PC-Wetterstation for arbitrary data.
    
    Args:
    data_folder:                Folder where the CSV-file for PC-Wetterstation will be stored. It must be given relative to the current path.
                                The file names will be automatically "EXP_MM_YY.CSV" with MM and YY being the months and the years of the datasets.
    rain_calib_factor:          Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
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
    key_list:                   List containing the order in which the datasets have to be written                            
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.

    Returns:
    file_list:                  List containing the names of all written files
    num_new_datasets:           Number of the new datasets merged into the existing data
    first_time:                 Timepoint of the first merged new dataset (datetime-object)
    last_time:                  Timepoint of the last merged new dataset (datetime-object)

    Raises:
    IOError:                    An error occurred accessing the file.
    """
    getmonth = lambda x: dt.strptime( x[3:], '%m.%Y' )
    getdate = lambda k: dt.strptime( k['date'] + ' ' + k['time'], '%d.%m.%Y %H:%M' )
    getdatestring = lambda k: k['date'] + ' ' + k['time']
    
    # determine the months existing in the data
    export_data.sort( key = getdatestring )
    days_set = { line['date'] for line in export_data }
    months_set = { getmonth(x) for x in days_set } 

    # write the data separately for each month into a file
    file_list = []
    for curr_month in months_set:
        monthly_days_set = { day for day in days_set if getmonth( day ) == curr_month }
        monthly_export_data = [ x for x in export_data if x['date'] in monthly_days_set ]
        file_list.append( writesinglemonth( data_folder, rain_calib_factor, station_name, station_height, station_type, monthly_export_data, key_list, sensor_list ) )

    if len( export_data ) > 0:
        first_time = getdate( export_data[0] )
        last_time = getdate( export_data[-1] )
    else:
        first_time = dt( datetime.MINYEAR, 1, 1, 0, 0, 0, 0 )
        last_time = dt( datetime.MINYEAR, 1, 1, 0, 0, 0, 0 )

    return file_list, len( export_data ), first_time, last_time


def writesinglemonth( data_folder, rain_calib_factor, station_name, station_height, station_type, export_data, key_list, sensor_list ):
    """Writes a CSV-file with the weather data compatible to PC-Wetterstation for a certain single month.
    
    Args:
    data_folder:                Folder where the CSV-file for PC-Wetterstation will be stored. It must be given relative to the current path.
                                The file name will be automatically "EXP_MM_YY.CSV" with MM and YY being the month and the year of the datasets.
    rain_calib_factor:          Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    station_name:               ID of the station (typically three letters, for example ERL).
    station_height:             Altitude of the station (in meters).
    station_type:               Information string on the detailed type of the weather station (producer, ...).
    export_data:                Data to be written on file. It must be only from one single month. It is required to be sorted regarding time.
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
    key_list:                   List containing the order in which the datasets have to be written                                      
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.

    Returns:
    file_name:                  Name of the written file

    Raises:
    IOError:                    An error occurred accessing the file.
    AssertionError:             The data in 'export_data' is from more than one month.
    """
    # Generate file name assuming that all datasets are from one month
    firstDate = dt.strptime( export_data[0]['date'], '%d.%m.%Y')
    file_name = data_file_tag + firstDate.strftime('%m_%y') + '.csv'
    data_file_name = data_folder + '/' + file_name

    # Generate settings line for the CSV-file
    settings_line = '#Calibrate=' + str( '%1.3f' % rain_calib_factor ) + ' #Regen0=0mm #Location=' + str( station_name ) + '/' + str( int( station_height ) ) + 'm #Station=' + station_type

    # Write header lines in a PC-Wetterstation compatible CSV-file
    with open( data_file_name, 'w', newline = '\r\n', encoding='latin-1' ) as f:
        for index, key in enumerate( key_list ):
            if index > 0:
                f.write(',')
            f.write( sensor_list[key][constants.name] )
        f.write( '\n' )
        for index, key in enumerate( key_list ):
            if index > 0:
                f.write( ',' )
            f.write( sensor_list[key][constants.unit] )
        f.write( '\n' )
        f.write( settings_line + '\n' )

    # Store all valid data in a PC-Wetterstation compatible CSV-file
    with open( data_file_name, 'a', newline='', encoding='latin-1' ) as f:
        writer = csv.writer( f, lineterminator="\r\n" )    

        # Write sensor indices line
        sensor_index_list = [ sensor_list[key][constants.export_index] for key in key_list ]
        writer.writerows( [ sensor_index_list ] );

        # Write data
        for line in export_data:
            data_output_line = [ line[key] for key in key_list ]
            writer.writerows( [ data_output_line ] )

    return file_name


def convertTo(read_data, last_old_rain_counter, sensor_list):
    """Converts weather data to units and format compatible to PC-Wetterstation.
    
    Args:
    read_data:                  List containing the new read data to be processed. For each time a list containing the data with the 
                                indices specified in 'sensor_list' must be present. It is not required to be sorted. 
                                The units of the data must be as follows:
                                    * time of measurement as standard c-time in seconds since epoch (CET considering daylight saving)
                                    * wind speeds in m/s
                                    * rain as absolute rain counter since the last reset at the measurement time (in tipping bucket counts)
                                    * temperatures in degree Celsius
                                    * pressure in hPa
                                    * humidities in percent
                                Invalid data is specified as 'i'.
    last_old_rain_counter:      Last rain counter setting before the first dataset of the new read data (in tipping bucket counts).
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in 'read_data'.
                                The keys must be identical to that used in the 'export_data'.
    
    Returns:
    export_data:                List containing the weather data compatible to PC-Wetterstation. The format is a list of ordered dicts 
                                with the key being registered in sensor_list. It contains at least the following information as strings in this order 
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
    last_dataset_rain_counter:  Rain counter setting of the last read dataset (in tipping bucket counts).

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
        line['windGusts'] = str( float( line['windGusts'] ) * 3.6 )     # convert from m/s to km/h
        line['windSpeed'] = str( float( line['windSpeed'] ) * 3.6 )     # convert from m/s to km/h
        line['windDir'] = str( float( line['windDir'] ) * 22.5 )        # convert to degree

    # Calculate rain amount differences
    rain_counters = [ float( line['rainCounter'] ) for line in export_data ]
    rain_counters.insert( 0, last_old_rain_counter )

    # Handle possible bug from the wetherstation giving occasionally invalid rain counter values
    for index, counter in enumerate( rain_counters[:] ):
        if index > 0:
            if ( counter - rain_counters[index-1] ) < 0:
                rain_counters[index] = rain_counters[index-1];

    rain_amounts = [ 0.68685 * ( x - rain_counters[i-1] ) for i, x in enumerate( rain_counters ) ][1:]              # convert from tipping bucket counts to mm
    for export_line, amount in zip( export_data[:], rain_amounts ):
        export_line['rainCounter'] = str( amount );                                                                 # set to rain amount differences since the last dataset before the current (in mm)

    last_dataset_time = dt.strptime( export_data[-1]['date'] + ' ' + export_data[-1]['time'], '%d.%m.%Y %H:%M')     # the accuracy is minutes
    last_dataset_rain_counter = rain_counters[-1]
    return export_data, last_dataset_time, last_dataset_rain_counter


def finddatafiles(data_folder):
    """Finds all PC-Wetterstation files in a given folder.
    
    Args:
    data_folder:                Folder in which the data files are searched. It can be a relative path to the current working directory. 
                                
    Returns:
    returns file_names:         A list containing all found PC-Wetterstation file names relative to 'data_folder' 
                               
    Raises:
    FileNotFoundError:          Risen if the data folder is not existing.
    """
    file_names = [ x for x in os.listdir( data_folder ) if x.find( data_file_tag ) != -1 ]

    return file_names


def deletedatafiles(data_folder, data_file_list):
    """Deletes all given files from a given folder.
    
    Args:
    data_folder:                Folder in which the data files are deleted. It can be a relative path to the current working directory. 
    data_file_list:             All files to be deleted in the folder 'data_folder'
                                
    Returns:
    None
                               
    Raises:
    FileNotFoundError:          Risen if the data folder is not existing.
    """
    for data_file in data_file_list:
        os.remove( data_folder + '/' + data_file )


def read( data_folder, file_name, sensor_list ):
    """Reads a CSV-file with the weather data compatible to PC-Wetterstation.
    
    Args:
    data_folder:                Folder where the CSV-file for PC-Wetterstation is be stored. It must be given relative to the current path.
    file_name:                  Name of the CSV-file, there are no requirements regarding the name.
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.  
    
    Returns:                             
    data:                       All data from the file. The format is a list of dicts with the keys being registered in sensor_list and given in 'key_list'. It contains at least 
                                the following information as strings:
                                    - date of the data in the format dd.mm.yyyy
                                    - time of the data (local time) in the format mm:hh
                                    - all measured data according to PC-Wetterstation specification with:
                                            * wind speeds in km/h
                                            * rain in mm since last recording
                                            * temperatures in degree Celsius
                                            * pressure in hPa
                                            * humidities in percent
    key_list:                   List containing all keys of 'data' in the order they are read from the file
    rain_calib_factor:          Calibration factor of the rain sensor (1.000 if the rain sensor has the original area).
    rain_counter_base:          Reference value of the rain counter before the start of the present data (in mm).
    station_name:               ID of the station (typically three letters, for example ERL).
    station_height:             Altitude of the station (in meters).
    station_type:               Information string on the detailed type of the weather station (producer, ...).
    sensor_descriptions_dict:   Dict containing the read descriptions of all sensors in the file. The keys are those from the sensor_list and are given in 'key_list'.
    sensor_units_dict:          Dict containing the read units of all sensors in the file. The keys are those from the sensor_list and are given in 'key_list'. 

    Raises:
    IOError:                    The file could not be opened.
    ImportError:                The file is not compatible to PC-Wetterstation
    """
    # Determine the sensors present in the file    
    file_name = data_folder + '/' + file_name
    with open( file_name, 'r', newline='', encoding='latin-1' ) as f:
        file_reader = csv.reader( f )

        # Read the three header lines
        sensor_descriptions = next( file_reader )
        sensor_units = next( file_reader )
        metadata = ','.join( next( file_reader ) )

        # Read first data line containing the sensor indices
        indices_list = next( file_reader )

    key_list = []
    for index in indices_list:
        curr_key = ''
        for key, sensor in sensor_list.items():
            if utilities.isFloat( index ):
                if sensor[constants.export_index] == int( index ):
                    curr_key = key
                    break
            else:
                break
        key_list.append( curr_key )

    # parse header lines # TODO: not all metadata entries must be present according to the specification!!!
    splitted_line = str.split( metadata, '#' )
    for line in splitted_line:
        line_pair = str.split( line, '=' )
        if line_pair[0] == 'Calibrate':
            rain_calib_factor = float( line_pair[1] )
        elif line_pair[0] == 'Regen0':
            line_pair[1].index( 'mm' )      # will raise an exception if the format is wrong
            rain_counter_base = float( line_pair[1].replace( 'mm', '' ) )
        elif line_pair[0] == 'Location':
            location_pair = str.split( line_pair[1], '/' )
            station_name = location_pair[0]
            location_pair[1].index( 'm' )   # will raise an exception if the format is wrong
            station_height = int( location_pair[1].replace( 'm', '' ) )
        elif line_pair[0] == 'Station':
            station_type = line_pair[1]

    # Handle the entries for date and time (by specification the first two entries)
    empty_entries = [ i for i, x in enumerate( key_list ) if x == '' ]
    if ( len( empty_entries ) != 2 ) or ( 0 not in empty_entries ) or ( 1 not in empty_entries ):
        raise ImportError( 'The file is no PC-Wetterstation compatible file' )
    key_list[0] = list( sensor_list.keys() )[0]
    key_list[1] = list( sensor_list.keys() )[1]
              
    # Read all weather data from the file
    with open( file_name, 'r', newline='', encoding='latin-1' ) as f:
        file_reader = csv.DictReader( f, key_list )

        # Skip all header lines
        next( file_reader )
        next( file_reader )
        next( file_reader )
        next( file_reader )

        # Read data
        data = list( file_reader )

    # Export sensor informations
    sensor_descriptions_dict = dict( [ ( key, sensor_descriptions[index] ) for index, key in enumerate( key_list ) ] )
    sensor_units_dict = dict( [ ( key, sensor_units[index] ) for index, key in enumerate( key_list ) ] )

    return data, key_list, rain_calib_factor, rain_counter_base, station_name, station_height, station_type, sensor_descriptions_dict, sensor_units_dict


def merge( out_data_folder, in_data_folder_1, input_file_name_1, in_data_folder_2, input_file_name_2, sensor_list, is_merge_only_new_data ):
    """Merges two CSV-files compatible to PC-Wetterstation.
    
    Args:
    out_data_folder:            Folder where the merged CSV-file for PC-Wetterstation is be stored. It must be given relative to the current path.
    in_data_folder_1:           Folder of the first input CSV-file to be merged.
    input_file_name_1:          Name of the first input CSV-file to be merged, there are no requirements regarding the name.
    in_data_folder_2:           Folder of the second input CSV-file to be merged.
    input_file_name_2:          Name of the second input CSV-file to be merged, there are no requirements regarding the name.
    sensor_list:                Ordered dict containing the mapping of all sensors to the index of the sensor in the weatherstation and the software PC-Wetterstation,
                                the name and the units of the sensors. The keys must be identical to that used in the 'export_data'.  
    is_merge_only_new_data:     Flag stating if only data in file 2 which is newer than the last entry in file 1 will be considered during the merging.
    
    Returns:                             
    output_data_file_list:      List containing all output files written. They are automatically named following the specification: 'EXP_MM_YY.csv'.
                                For each month an own file is written according to the specification. 
                                
    Raises:
    IOError:                    A file could not be opened.
    ImportError:                A file is not compatible to PC-Wetterstation or the files are inconsistent regarding sensor types or units.
    """
    getdate = lambda k: dt.strptime( k['date'] + ' ' + k['time'], '%d.%m.%Y %H:%M')

    # Import data files
    data_1, key_list_1, rain_calib_factor_1, rain_counter_base_1, station_name_1, station_height_1, station_type_1, sensor_descriptions_dict_1, sensor_units_dict_1 = read( in_data_folder_1, input_file_name_1, sensor_list )
    data_2, key_list_2, rain_calib_factor_2, rain_counter_base_2, station_name_2, station_height_2, station_type_2, sensor_descriptions_dict_2, sensor_units_dict_2 = read( in_data_folder_2, input_file_name_2, sensor_list )

    # Check if the files are from the identical station (the rain counter base does not need to be identical)
    if key_list_1 != key_list_2 or rain_calib_factor_1 != rain_calib_factor_2 or station_name_1 != station_name_2 or station_height_1 != station_height_2 or station_type_1 != station_type_2 or sensor_descriptions_dict_1 != sensor_descriptions_dict_2 or sensor_units_dict_1 != sensor_units_dict_2:
        raise ImportError( 'The stations are not identical.' )

    if is_merge_only_new_data:
        # Delete all datasets from file 2 which are not newer than the last timepoint in file 1 (assuming sorted files)
        last_time_1 = getdate( data_1[-1] ) 
        data_2 = [ line for line in data_2 if getdate( line ) > last_time_1 ]

    # Merge data unique but unsorted (during shifting of daylight saving the data in this time will be overwritten)
    merged_data = data_1 + data_2    
    temp_dict = {}   
    for line in merged_data:
        temp_dict[ line['date'] + ' ' + line['time'] ] = line
    merged_data = list( temp_dict.values() )

    # Write merged data in data files (one for each month)
    output_data_file_list = write( out_data_folder, rain_calib_factor_1, station_name_1, station_height_1, station_type_1, merged_data, key_list_1, sensor_list )

    return output_data_file_list[0]
