"""Reading weather data from TE923-stations.

Functions:
te923ToCSVreader:               Reads the weather data from a TE923-station and transfers it to a server using Wetterstation-compatible CSV-files.
reset_logger:                   Resets a logger instance.

Global variables:
log_file_name:                  Name of the log file where the status of the operations is stored (only relevant for Windows, under Linux the syslog is used)
station_type:                   Detailed name of the stations for which this script is working
sensor_list:                    List of all sensors read including the mapping to information in the Wetterstation CSV-files.
"""
from datetime import datetime as dt
from datetime import timedelta as timedelta
from collections import OrderedDict
import logging
import sys

import constants
import stationdata
import lastdata
import te923station
import pcwetterstation
import server

log_file_name = 'te923.log' # only relevant for Windows
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

delta_t_tol = timedelta( minutes = 60 ); # All datasets read from the weather station with a timestamp being more than this tolerance time in the future are dismissed


def reset_logger(logger):
    """Resets a logger instance.
    
    Args:
    logger:                     Logger instance to be reset

    Returns:
    None

    Raises:
    None
    """
    if sys.platform != 'linux':
        # Close the logger
        logger.handlers[0].stream.close()
        logger.removeHandler(logger.handlers[0])


def te923ToCSVreader(data_folder, station_data_file_name, script_name):
    """Reads the weather data from a TE923-station and transfers it to a server using Wetterstation-compatible CSV-files.
    
    Args:
    data_folder:                Operation directory of the function. Here all status files and the temporary data files are stored. Under Windows also the log-file is stored here.
    station_data_file_name:     Name of the file that contains all information on the weather station.
    script_name:                Name of the calling script (used for logging purposes)

    Returns:
    None

    Raises:
    None
    """
    firstNewDataIndex = 0

    # Start the logger
    logger = logging.getLogger()
    if sys.platform == 'linux':
        from logging.handlers import SysLogHandler
        syslog = SysLogHandler(address='/dev/log')
        formatter = logging.Formatter('%(name)s - %(app_name)s - %(levelname)s : %(message)s')
        syslog.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(syslog)
        logger = logging.LoggerAdapter(logger, { 'app_name': script_name } )
    else:
        logging.basicConfig( filename=log_file_name, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S' )

    try:
        # Read station data
        try:
            rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server, ftp_folder = stationdata.read( data_folder + '/' + station_data_file_name )
        except Exception as e:
            raise RuntimeError( 'Station data file could not be read. Error description: %s.', repr(e) )
        settings_file_name = 'settings_' + station_name + '.dat'
        try:
            is_reading, last_read_dataset_time, last_read_dataset_raincounter = lastdata.read( data_folder + '/' + settings_file_name )
        except Exception:
            # In this case it is assumed that the program is executed for the first time and all datasets should be read
            last_read_dataset_time = dt.min
            is_reading = False

        # Check if the station currently reads
        if is_reading:
            raise RuntimeError( 'Another instance is already reading from the weatherstation TE923. Skipping reading.' )

        # Notify other processes via the settings file of the reading in progress
        lastdata.set_reading( data_folder + settings_file_name, True )

        curr_time = dt.now()
        trunc_curr_time = dt( curr_time.year, curr_time.month, curr_time.day, curr_time.hour, curr_time.minute )
        trunc_last_read_dataset_time = dt( last_read_dataset_time.year, last_read_dataset_time.month, last_read_dataset_time.day, last_read_dataset_time.hour, last_read_dataset_time.minute )
        try:
            if ( trunc_curr_time - trunc_last_read_dataset_time ) < 2 * timedelta( minutes = storage_interval ):
                # Read only the current data
                imported_data = te923station.readdata( False )
            else:
                # Read all datasets from the weatherstation and after this the current dataset - as the reading of the full dataset usually takes longer than one storage cycle
                imported_data = te923station.readdata( True )
                imported_data = imported_data + te923station.readdata( False )
        except Exception as e:
            raise RuntimeError( 'Error accessing weatherstation TE923. Error description: %s.', repr(e) )

        if ( len( imported_data ) == 0 ):
            raise RuntimeError( 'No data could be read from the weather station. Maybe no USB-connection is possible.' )
        else:
            # Reduce datasets to unsaved new datasets (it is assumed that the read data is sorted according to time)
            date_index = sensor_list[ 'date' ][ constants.import_index ]
            imported_data = [ x for x in imported_data if ( dt.fromtimestamp( int( x[ date_index ] ) ) > last_read_dataset_time ) ]

            # Ensure that the data contains no timestamps in the future
            curr_time = dt.now() # Compare to the current system time
            imported_data = [ x for x in imported_data if ( dt.fromtimestamp( int( x[ date_index ] ) ) < curr_time + delta_t_tol ) ];
        
            if ( len( imported_data ) > 0 ):         
                # If this is the first execution of the program or the last stored data is older than three storage steps, there is no other choice than using the rain counter value of the first dataset as reference
                new_first_read_dataset_time = dt.fromtimestamp( int( imported_data[ firstNewDataIndex ][ sensor_list[ 'date' ][ constants.import_index ] ] ) );
                if ( new_first_read_dataset_time - last_read_dataset_time ) > 3 * timedelta( minutes = storage_interval ):
                    last_read_dataset_raincounter = float( imported_data[ firstNewDataIndex ][ sensor_list[ 'rainCounter' ][ constants.import_index ] ] )
  
                # Write weather data to PC-Wetterstation CSV-files
                export_data, last_dataset_time, last_dataset_rain_counter = pcwetterstation.convertTo( imported_data, last_read_dataset_raincounter, sensor_list )
                new_data_file_list, num_new_datasets, first_time, last_time = pcwetterstation.write( data_folder, rain_calib_factor, station_name, station_height, station_type, export_data, list( export_data[0].keys() ), sensor_list )
                logger.info( 'Found %i new weather datasets from %s - %s', num_new_datasets, first_time.strftime('%d.%m.%Y %H:%M'), last_time.strftime('%d.%m.%Y %H:%M') )

                # Transfer all CSV-files to the server
                data_file_list = pcwetterstation.finddatafiles( data_folder )
                try:
                    transfered_file_name = server.transferto( ftp_server, station_name, ftp_passwd, ftp_folder, data_folder, data_file_list )
                    isSuccessfullTransfer = True;
                except Exception as e:
                    error_text = repr( e )
                    isSuccessfullTransfer = False;

                # Delete the CSV-files in any situation
                pcwetterstation.deletedatafiles( data_folder, data_file_list )

                # Store the next latest dataset only if the transfer to the server was successfull, otherwise there is a rollback
                if ( isSuccessfullTransfer ):
                    # The reading flag is also resetted here by default
                    lastdata.write( data_folder + '/' + settings_file_name, last_dataset_time, last_dataset_rain_counter )
                    logger.info( 'Weather data in the files %s (%s) was successfully transfered to FTP-server \'%s\' (user: \'%s\').', data_file_list, transfered_file_name, ftp_server, station_name )
                else:
                    raise RuntimeError( 'Weather data transfer to FTP-server \'%s\' (user: \'%s\') failed. Read weather data in the files %s (%s) was discarded. Error description: %s.', ftp_server, station_name, data_file_list, transfered_file_name, error_text )
            else:
                raise RuntimeError( 'No weather data found which was unprocessed.' )
    except Exception as e:
        lastdata.set_reading( data_folder + '/' + settings_file_name, False )
        logger.error( repr(e) )
        reset_logger(logger)
        sys.exit()

    reset_logger(logger)
