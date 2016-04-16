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


"""Weather server reading incoming data and performing its processing.

Functions:
main:                           Main function of the weather server.

Global variables:
server_data_file_name:          Name of the server configuration file. It must be located in the same directory as this Python-file.
"""
import locale
import sys
import os.path
import logging
from zipfile import ZipFile

import csvfilemerger
import graphs
import serverdata


log_file_name = 'weatherserver.log' # only relevant for Windows
server_data_file_name = '/opt/weatherstation/configData/serverdata.dat'


def main():
    """Main function of the weather server.
    
    Arguments:
    sys.argv:                   The new data files to be processed must be given as command-line arguments (without path). More than one file can be passed.

    Remarks:
    Calling this program multiple while another instance of it is still processing data on a certain folder may lead to race conditions and must be prevented by the user.    

    Raises:
    None
    """
    # Load new data files from the command line arguments
    input_list = sys.argv
    script_name = input_list.pop(0)   # remove script name

    # Start the logger
    logger = logging.getLogger()
    if sys.platform.startswith('linux'):
        from logging.handlers import SysLogHandler
        syslog = SysLogHandler(address='/dev/log')
        formatter = logging.Formatter('%(name)s - %(app_name)s - %(levelname)s : %(message)s')
        syslog.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(syslog)
        logger = logging.LoggerAdapter(logger, { 'app_name': script_name } )
    else:
        logging.basicConfig( filename=log_file_name, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S' )

    if len( input_list ) < 1:
        logger.error( 'Starting via command line: No data files were passed.' )
        return

    # Read server configuration data
    data_storage_folder, ftp_base_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot = serverdata.read( server_data_file_name )

    # Determine the weather station name and the file names
    new_zip_data_file_list = [ os.path.basename( path ) for path in input_list ]
    new_dir_set = { os.path.dirname( path ) for path in input_list }
    new_dir_set = { str.replace( path, new_data_folder, '' ) for path in new_dir_set }
    new_dir_set = { os.path.dirname( path ) for path in new_dir_set }
    if ( len( new_dir_set ) > 1 ):
        logger.error( 'Starting via command line: Data from more than one station was passed.' )
        return
    station_name = os.path.basename( new_dir_set.pop() )

    # Construct the directory paths for the station
    data_storage_folder = data_storage_folder + '/' + station_name + '/'
    ftp_station_folder = ftp_base_folder + '/' + station_name + '/'
    new_data_folder = ftp_station_folder + '/' + new_data_folder + '/'
    temp_data_folder = new_data_folder + '/' + temp_data_folder + '/'
    graph_folder = graph_folder + '/' + station_name + '/'

    # Extract data from the ZIP-file(s)
    new_data_file_list = []
    for file in new_zip_data_file_list:
        with ZipFile( new_data_folder + '/' + file, 'r' ) as zip_file:
            new_data_file_list = new_data_file_list + zip_file.namelist()
            zip_file.extractall( temp_data_folder )

    # Merge the new data files into the existing storage CSV-files
    try:
        num_new_datasets, first_time, last_time = csvfilemerger.merge( new_data_file_list, temp_data_folder, temp_data_folder, data_storage_folder )
        logger.info( 'Merged %i new received dataset(s) (%s - %s) from the station \'%s\' (file(s): %s -> %s) into the data folder \'%s\'.' % ( num_new_datasets, 
                     first_time.strftime('%d.%m.%Y %H:%M'), last_time.strftime('%d.%m.%Y %H:%M'), station_name, new_zip_data_file_list, new_data_file_list, data_storage_folder ) )
    except Exception as e:
        logger.error( 'Merging new received dataset(s) from the station \'%s\' (file(s) %s -> %s) into the folder \'%s\' failed. Error description: %s.' % ( station_name, new_zip_data_file_list, new_data_file_list, data_storage_folder, repr(e) ) )
        return

    # Delete the ZIP-file(s)
    for file in new_zip_data_file_list:
        os.remove( new_data_folder + '/' + file )

    # Set German locale
    if sys.platform.startswith('linux'):
        locale.setlocale( locale.LC_ALL, 'de_DE.utf8' )
    elif sys.platform.startswith( 'win' ):
        locale.setlocale( locale.LC_ALL, 'german' )

    # Update the weather graphs in the station's folder
    try:
        num_plot_datasets, first_plot_time, last_plot_time = graphs.plot_of_last_n_days( 7, data_storage_folder, sensors_to_plot, graph_folder, graph_file_name, True )        
        logger.info( 'Plotted %i dataset(s) (%s - %s) from the station \'%s\' into the graphics file \'%s\' in the folder \'%s\'.' % ( num_plot_datasets, 
                     first_plot_time.strftime('%d.%m.%Y %H:%M'), last_plot_time.strftime('%d.%m.%Y %H:%M'), station_name, graph_file_name, graph_folder ) )
    except Exception as e:
        logger.error( 'Plotting the graph \'%s\' from the station \'%s\' into the plot graph folder \'%s\' with the data in \'%s\' failed. Error description: %s.' % ( graph_file_name, station_name, graph_folder, data_storage_folder, repr(e) ) )
        return

    
if __name__ == "__main__":
    main()




 
