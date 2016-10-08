import csv
from datetime import datetime as dt
from datetime import timedelta
import os
from weathernetwork.common.exceptions import PCWetterstationFileParseError, DatasetFormatError
from weathernetwork.common.sensor import CombiSensorData, BaseStationSensorData, WindSensorData, RainSensorData
from weathernetwork.common.weatherstationdataset import WeatherStationDataset


class PCWetterstationFormatFile(object):
    """Class for weather data files of the program PCWetterstation"""

    DATA_FILE_TAG = 'EXP'       # indicating a PC-Wetterstation data file

    def __init__(self, combi_sensor_IDs):
        """
        Constructor.
        :param combi_sensor_IDs:    contains a list with all combi sensor IDs that should be present in the file
        """
        # list of sensors defined for the PCWetterstation file format (see page 269 of the manual for PCWetterstation)
        self._sensor_list = []
        self._sensor_list.append( ([BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE], 133) )
        self._sensor_list.append( ([BaseStationSensorData.BASE_STATION, BaseStationSensorData.UV], 9) )
        self._sensor_list.append( ([WindSensorData.WIND, WindSensorData.AVERAGE], 35) )
        self._sensor_list.append( ([WindSensorData.WIND, WindSensorData.GUSTS], 45) )
        self._sensor_list.append( ([WindSensorData.WIND, WindSensorData.WIND_CHILL], 8) )
        self._sensor_list.append( ([WindSensorData.WIND, WindSensorData.DIRECTION], 36) )
        self._sensor_list.append( ([RainSensorData.RAIN, RainSensorData.PERIOD], 34) )

        # combi sensors defined by the user
        file_specific_temp_sensor_ID = 1 # temperature sensors have an ID of 1 .. 16 in PCWetterstation format files
        file_specific_humidity_sensor_ID = 17 # humidity sensors have an ID of 17 ... 32 in PC Wetterstation format files
        for combi_sensor in combi_sensor_IDs:
            self._sensor_list.append( ([combi_sensor, CombiSensorData.TEMPERATURE], file_specific_temp_sensor_ID) )
            self._sensor_list.append( ([combi_sensor, CombiSensorData.HUMIDITY], file_specific_humidity_sensor_ID) )
            file_specific_temp_sensor_ID += 1
            file_specific_humidity_sensor_ID += 1


    @staticmethod
    def deletedatafiles(data_folder, data_file_list):
        """
        Deletes all given files from a given folder.
    
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


    def read(self, file_name, delta_time):
        """
        Reads a CSV-file with the weather data compatible to PC-Wetterstation.
        :param delta_time:          time between two datasets (only relevant for the rain gauge data of the first dataset, where this information cannot be derived automatically), in minutes    
        Raises:
        IOError:                    The file could not be opened.
        ImportError:                The file is not compatible to PC-Wetterstation
        """
        try:
            # Determine the sensors present in the file    
            file_name = file_name
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
                    prev_time = time - timedelta(seconds=int(round( 60 * delta_time )))

                curr_dataset = WeatherStationDataset(time)
                curr_dataset.add_sensor(CombiSensorData( 'IN', line['Temp. I.'], line['Feuchte I.'] )) # TODO: generalize this with the available information on the required combi sensors
                curr_dataset.add_sensor(CombiSensorData( 'OUT1', line['Temp. A. 1'], line['Feuchte A. 1'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT2', line['Temp. A. 2'], line['Feuchte A. 2'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT3', line['Temp. A. 3'], line['Feuchte A. 3'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT4', line['Temp. A. 4'], line['Feuchte A. 4'] ))
                curr_dataset.add_sensor(CombiSensorData( 'OUT5', line['Temp. A. 5'], line['Feuchte A. 5'] ))

                curr_dataset.add_sensor(BaseStationSensorData(line['Luftdruck'], line['UV-X']))
                curr_dataset.add_sensor(RainSensorData(line['Regen'], prev_time)) # cumulated data is not available here
                curr_dataset.add_sensor(WindSensorData(line['Wind'], line['Windböen'], line['Richtung'], line['Temp. Wind']))
                datasets.append(curr_dataset)

            return datasets, rain_calib_factor, rain_counter_base, station_name, station_height, station_type # TODO: replace the station data by a WeatherStationMetadata object!!!!
        except Exception as e:
            raise PCWetterstationFileParseError("Weather data file \"%s\" has invalid format." % file_name)


    def write(self, file_path, data, station_metadata):
        """Writes a CSV-file with the weather data compatible to PC-Wetterstation.
    
        Args:
        file_path:                  Path where the CSV-file will be written to.
        data:                       Weather data to be written to file. It is expected to be sorted by ascending time.
        station_metadata            Metadata of the station
        """
        # generate settings line for the CSV-file
        settings_line = self._create_settings_header_line(station_metadata)

        dataset_index = 0
        while dataset_index < len(data):
            # generate file name based on the first dataset
            first_date = data[dataset_index].get_time()
            file_name = PCWetterstationFormatFile.DATA_FILE_TAG + first_date.strftime('%m_%y') + '.csv'
            data_file_name = file_path + '/' + file_name
        
            # store all data of this month in a PC-Wetterstation compatible CSV-file
            is_first = True
            with open(data_file_name, 'w', newline='', encoding='latin-1') as f:
                writer = csv.writer(f, lineterminator="\r\n")    

                for dataset in data[dataset_index:]:
                    if not self._in_same_month(dataset.get_time(), first_date):
                        break

                    values, description_list, unit_list, sensor_list = self._get_line(dataset)
                    if is_first:
                        # write the header lines
                        writer.writerow(description_list)
                        writer.writerow(unit_list)
                        writer.writerow([settings_line])
                        writer.writerow(sensor_list)
                        is_first = False

                    writer.writerow(values)
                    dataset_index += 1


    def _in_same_month(self, first_date, second_date):
        """
        Determines if the two dates are within the same month.
        """
        if first_date.month == second_date.month and first_date.year == second_date.year:
            return True
        else:
            return False


    def _create_settings_header_line(self, station_metadata):
        """
        Helper method for creating the settings header line of a PCWetterstation CSV-file.
        """
        station_ID = station_metadata.get_station_ID()
        location = station_metadata.get_location_info()
        station_latitude, station_longitude, station_height = station_metadata.get_geo_info()
        device_info = station_metadata.get_device_info()
        rain_calib_factor = station_metadata.get_rain_calib_factor()

        settings_line = '#Calibrate=' + str( '%1.3f' % rain_calib_factor ) + ' #Regen0=0mm #Location=' + str( location ) + ' (' + str( station_latitude ) + '\N{DEGREE SIGN}/' + \
            str( station_longitude ) + '\N{DEGREE SIGN}) ' + '/ ' + str( int( station_height ) ) + 'm #Station=' + str( station_ID ) + " (" + device_info + ")"

        return settings_line


    def _get_line(self, dataset):
        """
        Helper method for preparing a single data line to be written into a CSV-file.
        """
        values = []
        sensor_list = []
        description_list = []
        unit_list = []

        # read the date and time
        time = dataset.get_time()
        values.append(time.strftime('%d.%m.%Y'))
        sensor_list.append("")
        description_list.append("date")
        unit_list.append("")

        values.append(time.strftime('%H:%M:%S'))
        sensor_list.append("")
        description_list.append("time")
        unit_list.append("")

        # read all sensor data
        for required_sensor in self._sensor_list:
            sensor_ID_list, sensor_format_specific_ID = required_sensor
            try:
                values.append( dataset.get_sensor_value(sensor_ID_list) )
                description_list.append( dataset.get_sensor_description(sensor_ID_list) )
                unit_list.append( dataset.get_sensor_unit(sensor_ID_list) )
                sensor_list.append( sensor_format_specific_ID )
            except:
                raise DatasetFormatError("Sensor %s is missing in the data to be written to file" % str(sensor_ID_list))

        return values, description_list, unit_list, sensor_list