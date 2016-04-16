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


"""Handles the storage of information of the weather data server.

Functions:
read:               Reads the storage file.
write:              Writes the storage file.
"""
import pickle


def write(server_file_name, data_storage_folder, ftp_base_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot):
    """Writes the data of the weather station.

    Args:
    server_file_name:      		The filename of the server data file (relative to the current path).
    data_storage_folder:        Path to the base folder where the storage (database-like) CSV-files are stored. The data for the different stations is located in subfolders with the station's names.
	ftp_base_folder:			Path to the base folder of the virtual FTP-server (absolute path). The data for the different stations is located in subfolders with the station's names.
    new_data_folder:            Name of the folder where the new data files are stored within the station subfolders on the FTP-server.
    temp_data_folder:           Name of the folder where the merger can store temporary files (within the 'new_data_folder').
    graph_folder:               Base folder where the graph plot file will be stored, the date for each station will be located in a subfolder with its name.    
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.    
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.

    Returns:
    None

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( server_file_name, 'wb' ) as f:
        pickle.dump( dict( data_storage_folder = data_storage_folder, ftp_base_folder = ftp_base_folder, new_data_folder = new_data_folder, temp_data_folder = temp_data_folder,
                          graph_folder = graph_folder, graph_file_name = graph_file_name, sensors_to_plot = sensors_to_plot ), f )


def read(server_file_name):
    """Returns the data of the weather station.

    Args:
    server_file_name:  			The filename of the server data file (relative to the current path).

    Returns:
    data_storage_folder:        Path to the base folder where the storage (database-like) CSV-files are stored. The data for the different stations is located in subfolders with the station's names.
	ftp_base_folder:			Path to the base folder of the virtual FTP-server (absolute path). The data for the different stations is located in subfolders with the station's names.
    new_data_folder:            Name of the folder where the new data files are stored within the station subfolders on the FTP-server.
    temp_data_folder:           Name of the folder where the merger can store temporary files (within the 'new_data_folder').
    graph_folder:               Base folder where the graph plot file will be stored, the date for each station will be located in a subfolder with its name.    
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.    
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.

    Raises:
    IOError:                    An error occurred accessing the file.
    """
    with open( server_file_name, 'rb') as f:
        data = pickle.load( f );   
            
        data_storage_folder = data['data_storage_folder']
        ftp_base_folder = data['ftp_base_folder']
        new_data_folder = data['new_data_folder']
        temp_data_folder = data['temp_data_folder']
        graph_folder = data['graph_folder']
        graph_file_name = data['graph_file_name']
        sensors_to_plot = data['sensors_to_plot']

    return data_storage_folder, ftp_base_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot