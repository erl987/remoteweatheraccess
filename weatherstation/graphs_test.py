"""Provides unit tests for the graph drawing module.

Unit tests:
test_plot_of_last_n_days:		Test for the plotting of the graph for the last n days.

Global variables:
data_folder:                    Path to the test data folder.
graph_file_name:                Name of the graph file to be stored.
"""
import unittest

import graphs

data_folder = './data'
graph_file_name = 'graph.svg'


class Test_graphs(unittest.TestCase):
    def setUp(self):
        '''Sets up each unit test.'''


    def test_plot_of_last_n_days(self):
        sensors_to_plot = [ 'pressure', 'rainCounter', 'tempOutside1', 'humidOutside1' ]
        graphs.plot_of_last_n_days( 7, data_folder, sensors_to_plot, data_folder, graph_file_name )     


    def tearDown(self):
        '''Finishes each unit test.'''

if __name__ == '__main__':
    unittest.main()






