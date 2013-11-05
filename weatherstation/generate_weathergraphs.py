"""Generates the weather graphs."""
import graphs
import locale
import sys

data_folder = './data'
graph_folder = './data'
graph_file_name = 'graph.svg'

# Set German locale
if sys.platform == 'linux':
    locale.setlocale( locale.LC_ALL, 'de_DE.utf8' )
elif sys.platform.startswith( 'win' ):
    locale.setlocale( locale.LC_ALL, 'german' )

# Generate graph of the last seven days
sensors_to_plot = [ 'pressure', 'rainCounter', 'tempOutside1', 'humidOutside1' ]
graphs.plot_of_last_n_days( 7, data_folder, sensors_to_plot, graph_folder, graph_file_name, True )     
