import te923ToCSVreader
import te923station
import unittest
from unittest.mock import Mock


data_folder = './data/'
station_data_file_name = 'stationData.dat'

class TestProcessToCSV(unittest.TestCase):

    def test_proces_to_csv(self):
        # replace reading from USB-weather station with mock object
        te923station.readdata = Mock( return_value = 
                                          [ [ '1381578982', '21.75', '51', '7.30', '92', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1016.4', '3.4', '5', '0', '13', '15.2', '23.2', '5.2', '920' ],
                                            [ '1381578920', '22.34',' 59', '8.30', '91', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1014.4', '2.1', '5', '0', '1', '7.8', '20.9', '23.4', '900' ],
                                            [ '1380577982', '21.32', '62', '6.30', '95', 'i', 'i', 'i', 'i', 'i', 'i', 'i', 'i', '1012.4', '6.4', '5', '0', '15', '43.5', '3.4', '2.1', '882'] ] )
        te923ToCSVreader.te923ToCSVreader( data_folder, station_data_file_name )
        
        # TODO: define test criterium


if __name__ == '__main__':
    unittest.main()