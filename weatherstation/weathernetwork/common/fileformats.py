from abc import ABCMeta, abstractmethod
import csv
from datetime import datetime as dt
from datetime import timedelta
import os
from weathernetwork.common.exceptions import PCWetterstationFileParseError
from weathernetwork.common.sensor import CombiSensorData, BaseStationSensorData, WindSensorData, RainSensorData
from weathernetwork.common.weatherstationdataset import WeatherStationDataset


class IWeatherDataFile(metaclass=ABCMeta):
    """Interface class for weather data files"""

    @abstractmethod
    def read(self):
        pass


class PCWetterstationFormatFile(IWeatherDataFile):
    """Class for weather data files of the program PCWetterstation"""

    def __init__(self, file_path, file_name, delta_time):
        """
        Constructor.
        :param delta_time:          time between two datasets (only relevant for the rain gauge data of the first dataset, where this information cannot be derived automatically), in minutes
        """
        self._file_path = file_path
        self._file_name = file_name
        self._delta_time = delta_time


    @staticmethod
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
            file_path = data_folder + '/' + data_file
            if os.path.isfile(file_path):
                os.remove(file_path)


    def read(self):
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
        try:
            # Determine the sensors present in the file    
            file_name = self._file_path + '/' + self._file_name
            with open( file_name, 'r', newline='', encoding='latin-1' ) as f:
                file_reader = csv.reader( f )

                # Read the three header lines
                sensor_descriptions = next( file_reader )
                sensor_units = next( file_reader )
                metadata = ','.join( next( file_reader ) )

                # Read first data line containing the sensor indices
                indices_list = next( file_reader )
                
                # check for correct number of header lines
                checked_indices_list = [x for x in indices_list if x.isdigit()]
                if indices_list[0] != '' or indices_list[1] != '':
                    raise PCWetterstationFileParseError("File header has invalid number of lines.")

                if ( len(checked_indices_list) + 2 ) != len(indices_list):
                    raise PCWetterstationFileParseError("File header has invalid number of lines.")
                
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
              
            # Read all weather data from the file
            with open( file_name, 'r', newline='', encoding='latin-1' ) as f:
                file_reader = csv.DictReader( f, sensor_descriptions )

                # Skip all header lines
                next( file_reader )
                next( file_reader )
                next( file_reader )
                next( file_reader )

                # Read data
                data = list( file_reader )

            # convert the sensor informations to a WeatherDataset object
            datasets = []
            for line in data:
                if 'time' in locals():
                    prev_time = time            
                time = dt.strptime( line['Datum'] + ' ' + line['Zeit'], '%d.%m.%Y %H:%M' )
                if not 'prev_time' in locals():
                    prev_time = time - timedelta(seconds=int(round( 60 * self._delta_time )))

                curr_dataset = WeatherStationDataset(time)
                curr_dataset.add_sensor(CombiSensorData( 'IN', line['Temp. I.'], line['Feuchte I.'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT1', line['Temp. A. 1'], line['Feuchte A. 1'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT2', line['Temp. A. 2'], line['Feuchte A. 2'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT3', line['Temp. A. 3'], line['Feuchte A. 3'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT4', line['Temp. A. 4'], line['Feuchte A. 4'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT5', line['Temp. A. 5'], line['Feuchte A. 5'] ))

                curr_dataset.add_sensor(BaseStationSensorData(line['Luftdruck'], line['UV-X']))
                curr_dataset.add_sensor(RainSensorData(line['Regen'], prev_time)) # cumulated data is not available here
                curr_dataset.add_sensor(WindSensorData(line['Wind'], line['Windböen'], line['Richtung'], line['Temp. Wind']))
                datasets.append(curr_dataset)

            return datasets, rain_calib_factor, rain_counter_base, station_name, station_height, station_type
        except Exception as e:
            raise PCWetterstationFileParseError("Weather data file \"%s\" has invalid format." % file_name)



