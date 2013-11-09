"""Handles the storage of information of the weather data server.

Functions:
read:               Reads the storage file.
write:              Writes the storage file.
"""
import pickle


def write(server_file_name, data_storage_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot):
    """Writes the data of the weather station.

    Args:
    server_data_file_name:      The filename of the server data file (relative to the current path).
    data_storage_folder:        Path to the base folder where the storage (database-like) CSV-files are stored. The data for the different stations is located in subfolders with the station's names.
    new_data_folder:            Path to the folder where the new data files are stored. Relative to 'data_storage_folder'.
    temp_data_folder:           Path to the folder where the merger can store temporary files. Relative to 'data_storage_folder', it must be different from the 'new_data_folder'.
    graph_folder:               Base folder where the graph plot file will be stored, the date for each station will be located in a subfolder with its name.    
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.    
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.

    Returns:
    None

    Raises:
    IOError:                An error occurred accessing the file.
    """
    with open( server_file_name, 'wb' ) as f:
        pickle.dump( dict( data_storage_folder = data_storage_folder, new_data_folder = new_data_folder, temp_data_folder = temp_data_folder,
                          graph_folder = graph_folder, graph_file_name = graph_file_name, sensors_to_plot = sensors_to_plot ), f )


def read(server_file_name):
    """Returns the data of the weather station.

    Args:
    server_data_file_name:  The filename of the server data file (relative to the current path).

    Returns:
    data_storage_folder:        Path to the base folder where the storage (database-like) CSV-files are stored. The data for the different stations is located in subfolders with the station's names.
    new_data_folder:            Path to the folder where the new data files are stored. Relative to 'data_storage_folder'.
    temp_data_folder:           Path to the folder where the merger can store temporary files. Relative to 'data_storage_folder', it must be different from the 'new_data_folder'.
    graph_folder:               Base folder where the graph plot file will be stored, the date for each station will be located in a subfolder with its name.  
    graph_file_name:            Name of the graph plot file. Any graphics format supported by MATPLOTLIB can be used, for example '.svg' or '.png'.    
    sensors_to_plot:            List with all names of the sensors to be plotted. The names must be identical with the 'sensor_list' dictionary labels.

    Raises:
    IOError:                    An error occurred accessing the file.
    """
    with open( server_file_name, 'rb') as f:
        data = pickle.load( f );   
            
        data_storage_folder = data['data_storage_folder']
        new_data_folder = data['new_data_folder']
        temp_data_folder = data['temp_data_folder']
        graph_folder = data['graph_folder']
        graph_file_name = data['graph_file_name']
        sensors_to_plot = data['sensors_to_plot']

    return data_storage_folder, new_data_folder, temp_data_folder, graph_folder, graph_file_name, sensors_to_plot