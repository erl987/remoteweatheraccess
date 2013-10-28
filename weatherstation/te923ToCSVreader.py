from datetime import datetime as dt
from datetime import timedelta as timedelta
from collections import OrderedDict
import logging

import constants
import stationdata
import lastdata
import te923station
import pcwetterstation
import server


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


def te923ToCSVreader(data_folder, station_data_file_name, log_file_name):
    firstNewDataIndex = 0

    # Start the logger
    logger = logging.getLogger()
    logging.basicConfig( filename= data_folder + log_file_name, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S' )

    # Read station data
    rain_calib_factor, station_name, station_height, storage_interval, ftp_passwd, ftp_server = stationdata.read( data_folder + station_data_file_name )
    settings_file_name = 'settings_' + station_name + '.dat'
    try:
        last_read_dataset_time, last_read_dataset_raincounter = lastdata.read( data_folder + settings_file_name )
    except Exception:
        # In this case it is assumed that the program is executed for the first time and all datasets should be read
        last_read_dataset_time = dt.min

    # Read all datasets from the weatherstation
    imported_data = te923station.readdata( True )

    if ( len( imported_data ) == 0 ):
        logging.warning( 'No data could be read from the weather station. Maybe no USB-connection is possible' )
    else:
        # Reduce datasets to unsaved new datasets (it is assumed that the read data is sorted according to time)
        date_index = sensor_list[ 'date' ][ constants.import_index ]
        imported_data = [ x for x in imported_data if ( dt.fromtimestamp( int( x[ date_index ] ) ) > last_read_dataset_time ) ]
        
        if ( len( imported_data ) > 0 ):         
            # If this is the first execution of the program or the last stored data is older than three storage steps, there is no other choice than using the rain counter value of the first dataset as reference
            new_first_read_dataset_time = dt.fromtimestamp( int( imported_data[ firstNewDataIndex ][ sensor_list[ 'date' ][ constants.import_index ] ] ) );
            if last_read_dataset_time == dt.min or ( new_first_read_dataset_time - last_read_dataset_time ) > 3 * timedelta( minutes = storage_interval ):
                last_read_dataset_raincounter = float( imported_data[ firstNewDataIndex ][ sensor_list[ 'rainCounter' ][ constants.import_index ] ] )
  
            # Write weather data to PC-Wetterstation CSV-files
            export_data, last_dataset_time, last_dataset_rain_counter = pcwetterstation.convertTo( imported_data, last_read_dataset_raincounter, sensor_list )
            pcwetterstation.write( data_folder, rain_calib_factor, station_name, station_height, station_type, export_data, sensor_list )
            logging.info( 'Found %i new weather datasets from %s - %s', len( export_data ), 
                         ( last_read_dataset_time + timedelta( minutes = storage_interval) ).strftime('%d.%m.%Y %H:%M'), last_dataset_time.strftime('%d.%m.%Y %H:%M') )

            # Transfer all CSV-files to the server
            data_file_list = pcwetterstation.finddatafiles( data_folder )
            try:
                server.transferto( ftp_server, station_name, ftp_passwd, data_folder, data_file_list )
                isSuccessfullTransfer = True;
            except Exception:
                isSuccessfullTransfer = False;

            # Delete the CSV-files in any situation
            pcwetterstation.deletedatafiles( data_folder, data_file_list )

            # Store the nex latest dataset only if the transfer to the server was successfull, otherwise there is a rollback
            if ( isSuccessfullTransfer ):
                lastdata.write( data_folder + settings_file_name, last_dataset_time, last_dataset_rain_counter )
                logging.info( 'Weather data was successfully transfered to FTP-server \'%s\' (user: \'%s\')', ftp_server, station_name )
            else:
                logging.error( 'Weather data transfer to FTP-server \'%s\' (user: \'%s\') failed. Read weather data was discarded', ftp_server, station_name )
        else:
            logging.info( 'No weather data found which was unprocessed' )

    # Close the logger
    logger.handlers[0].stream.close()
    logger.removeHandler(logger.handlers[0])
