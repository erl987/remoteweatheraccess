"""Weather server reading incoming data and performing its processing.

Functions:
main:                           Main function of the weather server.

Global variables:
server_data_file_name:          Name of the server configuration file. It must be located in the same directory as this Python-file.
"""
import locale
import sys
import os.path

import csvfilemerger
import graphs
import serverdata


server_data_file_name = '/home/ernbg/csvfilemerger/serverdata.dat'


def main():
    """Main function of the weather server.
    
    Arguments:
    sys.argv:                   The new data files to be processed must be given as command-line arguments (without path). More than one file can be passed.

    Remarks:
    Calling this program multiple while another instance of it is still processing data on a certain folder may lead to race conditions and must be prevented by the user.    

    Raises:
    RuntimeError:               Risen if the command-line parameters are not correct.
    """
    # Load new data files from the command line arguments
    if ( len(sys.argv) == 1 ):
        raise RuntimeError( 'The new files must be given as command line arguments.' )
    input_list = sys.argv
    input_list.pop(0)   # remove script name

    # Read server configuration data
    data_storage_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot = serverdata.read( server_data_file_name )

    # Determine the weather station name and the file names
    new_data_file_list = [ os.path.basename( path ) for path in input_list ]
    new_dir_set = { os.path.dirname( path ) for path in input_list }
    new_dir_set = { str.replace( path, new_data_folder, '' ) for path in new_dir_set }
    new_dir_set = { os.path.dirname( path ) for path in new_dir_set }
    if ( len( new_dir_set ) > 1 ):
        raise RuntimeError( 'The files given via command line must be from one single station.' )
    station_name = os.path.basename( new_dir_set.pop() )

    # Construct the directory paths for the station
    data_storage_folder = data_storage_folder + '/' + station_name + '/'
    new_data_folder = data_storage_folder + new_data_folder
    temp_data_folder = data_storage_folder + temp_data_folder
    graph_folder = graph_folder + '/' + station_name

    # Merge the new data files into the existing storage CSV-files
    csvfilemerger.merge( new_data_file_list, new_data_folder, temp_data_folder, data_storage_folder )

    # Set German locale
    if sys.platform == 'linux':
        locale.setlocale( locale.LC_ALL, 'de_DE.utf8' )
    elif sys.platform.startswith( 'win' ):
        locale.setlocale( locale.LC_ALL, 'german' )

    # Update the weather graphs in the station's folder
    graphs.plot_of_last_n_days( 7, data_storage_folder, sensors_to_plot, graph_folder, graph_file_name, True )        

    
if __name__ == "__main__":
    main()




 
