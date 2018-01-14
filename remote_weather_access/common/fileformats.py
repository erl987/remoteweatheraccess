# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
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

import csv
import os
from collections import OrderedDict
from datetime import datetime as dt
from datetime import timedelta

from remote_weather_access.common.utilities import extract_bracket_contents
from remote_weather_access.common.exceptions import PCWetterstationFileParseError, DatasetFormatError
from remote_weather_access.common.datastructures import CombiSensorData, BaseStationSensorData, WindSensorData, RainSensorData
from remote_weather_access.common.datastructures import WeatherStationMetadata, WeatherStationDataset


class PCWetterstationFormatFile(object):
    """Class for processing weather data files having the format for the program PC-Wetterstation.
    Only the english CSV-format is accepted.
    """

    _DATA_FILE_TAG = 'EXP'  # indicating a PC-Wetterstation data file
    _DATE = "date"  # constant describing a date (equivalent to the sensor IDs)
    _TIME = "time"  # constant describing a time of day (equivalent to the sensor IDs)

    def __init__(self, combi_sensor_ids, combi_sensor_descriptions):
        """
        Constructor.

        :param combi_sensor_ids:                contains a list with all combi sensor IDs in the same order as they
                                                are / will be present in the file. The headings in the file are
                                                ignored.
        :type combi_sensor_ids:                 list of strings
        :param combi_sensor_descriptions:       descriptions of the combi sensors (with the combi sensor IDs as keys)
        :type combi_sensor_descriptions:        dict(string, string)
        :raise PCWetterstationFileParseError:   if more combi sensors than allowed are defined
        """
        # list of required sensors, using the PCWetterstation file format based sensor IDs
        # (see page 269 of the manual for PCWetterstation)
        self._sensor_list = OrderedDict()
        self._sensor_list[(BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE)] = 133
        self._sensor_list[(BaseStationSensorData.BASE_STATION, BaseStationSensorData.UV)] = 9
        self._sensor_list[(WindSensorData.WIND, WindSensorData.AVERAGE)] = 35
        self._sensor_list[(WindSensorData.WIND, WindSensorData.GUSTS)] = 45
        self._sensor_list[(WindSensorData.WIND, WindSensorData.WIND_CHILL)] = 8
        self._sensor_list[(WindSensorData.WIND, WindSensorData.DIRECTION)] = 36
        self._sensor_list[(RainSensorData.RAIN, RainSensorData.PERIOD)] = 34

        # required combi sensors defined by the user
        self._combi_sensor_IDs = combi_sensor_ids
        self._combi_sensor_descriptions = combi_sensor_descriptions
        file_specific_temperature_sensor_id = 1  # temperature sensors have an ID of 1 .. 16 in PCWetterstation files
        file_specific_humidity_sensor_id = 17  # humidity sensors have an ID of 17 ... 32 in PC Wetterstation files
        for combi_sensor in combi_sensor_ids:
            self._sensor_list[(combi_sensor, CombiSensorData.TEMPERATURE)] = file_specific_temperature_sensor_id
            self._sensor_list[(combi_sensor, CombiSensorData.HUMIDITY)] = file_specific_humidity_sensor_id
            file_specific_temperature_sensor_id += 1
            file_specific_humidity_sensor_id += 1

            if file_specific_temperature_sensor_id > 16:
                raise PCWetterstationFileParseError("More combi sensors than allowed by the file format.")

    @staticmethod
    def delete_datafiles(data_folder, data_file_list):
        """
        Deletes all given files from a given folder.

        :param data_folder:                     folder where all given files should be deleted.
                                                It can be a relative path to the current working directory.
        :type data_folder:                      string
        :param data_file_list:                  list containing all files to be deleted
        :type data_file_list:                   list of strings
        :raise FileNotFoundError:               if the data folder is not existing
        """
        for data_file in data_file_list:
            file_path = data_folder + '/' + data_file
            if os.path.isfile(file_path):
                os.remove(file_path)

    def read(self, file_name, station_id, delta_time=10):
        """
        Reads a PC-Wetterstation format file.

        :param file_name:                       path and name of the data file. It can be a relative path to the
                                                current working directory.
        :type file_name:                        string
        :param station_id:                      ID of the weather station for which the data is valid
        :type station_id:                       string
        :param delta_time:                      time between two datasets in minutes (only relevant for the rain gauge
                                                data of the first dataset, where this information cannot be derived
                                                automatically)
        :type delta_time:                       float
        :return:                                weather datasets, rain counter base, station metadata,
                                                first time of dataset, last time of dataset
        :rtype:                                 tuple(WeatherStationDataset, float, WeatherStationMetadata,
                                                datetime, datetime)
        :raise FileNotFoundError:               if the file does not exist
        :raise PCWetterstationFileParserError:  if the file could not be parsed
        """
        time = None
        prev_time = None
        first_time = dt.max
        last_time = dt.min

        if not os.path.isfile(file_name):
            raise FileNotFoundError("The file '{}' does not exist".format(file_name))

        try:
            with open(file_name, 'r', newline='', encoding='latin-1') as f:
                file_reader = csv.reader(f)

                # read the four header lines
                next(file_reader)   # sensor descriptions
                next(file_reader)   # sensor units
                metadata = ','.join(next(file_reader))
                station_metadata, rain_counter_base = self._parse_file_metadata(metadata, station_id)
                indices_list = next(file_reader)

                # check for correct file format
                checked_indices_list = self._check_file_format(indices_list)

                # read all weather data from the file at once (the keys are the format internal sensor IDs)
                file_reader = csv.DictReader(f, [PCWetterstationFormatFile._DATE,
                                                 PCWetterstationFormatFile._TIME] + checked_indices_list)
                data = list(file_reader)

                # parse the weather data line by line
                datasets = []
                for single_line_dict in data:
                    if time:
                        prev_time = time

                    date_string = single_line_dict[PCWetterstationFormatFile._DATE]
                    time_string = single_line_dict[PCWetterstationFormatFile._TIME]
                    time = dt(*map(int, [date_string[6:], date_string[3:5], date_string[0:2], time_string[:2],
                                         time_string[3:]]))  # performance optimized
                    if not prev_time:
                        first_time = time
                        prev_time = time - timedelta(
                            seconds=int(round(60 * delta_time)))  # initial guess for the first timepoint in the file

                    datasets.append(self._parse_single_line(time, prev_time, single_line_dict))
                if time:
                    last_time = time

            return datasets, rain_counter_base, station_metadata, first_time, last_time
        except Exception as e:
            raise PCWetterstationFileParseError("Weather data file \"%s\" has invalid format: %s" % (file_name, str(e)))

    def _check_file_format(self, indices_list):
        """
        Checks for the validity of the file format.

        :param indices_list:                    list containing all (PC-Wetterstation internal) indices of the
                                                sensors present in the file
        :type indices_list:                     list of strings (containing integers)
        :return:                                list of all (PC-Wetterstation internal) indices that could be verified
                                                to be present in the file
        :rtype:                                 list of integers
        :raise PCWetterstationParseError:       if the sensors indices are not consistent
        """
        checked_indices_list = [int(x) for x in indices_list if x.isdigit()]

        if indices_list[0] != '' or indices_list[1] != '':
            raise PCWetterstationFileParseError("File header format is invalid")
        if (len(checked_indices_list) + 2) != len(indices_list):
            raise PCWetterstationFileParseError("File header format is invalid")
        if not set(self._sensor_list.values()) <= set(checked_indices_list):
            raise PCWetterstationFileParseError("File does not contain all required sensors")

        return checked_indices_list

    def _parse_single_line(self, time, prev_time, data_dict):
        """
        Parses the data from a single line in a PCWetterstation file to a WatherstationDataset-object.

        :param time:                            timepoint for which the current data is valid
        :type time:                             datetime.datetime
        :param prev_time:                       previous timepoint before the current data is valid
        :type prev_time:                        datetime.datetime
        :param data_dict:                       all data for the present time point
        :type data_dict:                        dict with the (PC-Wetterstation internal) sensors being the keys
        :return:                                weather dataset
        :rtype:                                 WeatherStationDataset
        :raise PCWetterstationFileParseError:   if the data could not be parsed
        """
        try:
            dataset = WeatherStationDataset(time)
            for combi_sensor in self._combi_sensor_IDs:
                description = self._combi_sensor_descriptions[combi_sensor]
                temperature = float(data_dict[self._sensor_list[(combi_sensor, CombiSensorData.TEMPERATURE)]])
                humidity = float(data_dict[self._sensor_list[(combi_sensor, CombiSensorData.HUMIDITY)]])
                dataset.add_sensor(CombiSensorData(combi_sensor, temperature, humidity, description))

            # required sensors
            pressure = float(
                data_dict[self._sensor_list[(BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE)]])
            uv = float(data_dict[self._sensor_list[(BaseStationSensorData.BASE_STATION, BaseStationSensorData.UV)]])
            dataset.add_sensor(BaseStationSensorData(pressure, uv))

            rain = float(data_dict[self._sensor_list[(RainSensorData.RAIN, RainSensorData.PERIOD)]])
            dataset.add_sensor(RainSensorData(rain, prev_time))  # cumulated data is not available here

            average = float(data_dict[self._sensor_list[(WindSensorData.WIND, WindSensorData.AVERAGE)]])
            gusts = float(data_dict[self._sensor_list[(WindSensorData.WIND, WindSensorData.GUSTS)]])
            direction = float(data_dict[self._sensor_list[(WindSensorData.WIND, WindSensorData.DIRECTION)]])
            wind_chill = float(data_dict[self._sensor_list[(WindSensorData.WIND, WindSensorData.WIND_CHILL)]])
            dataset.add_sensor(WindSensorData(average, gusts, direction, wind_chill))
        except Exception as e:
            raise PCWetterstationFileParseError("Data parsing error: %s" % str(e))

        return dataset

    @staticmethod
    def _parse_file_metadata(metadata, station_id):
        """
        Parses the metadata information of a PCWetterstation format file.

        :param metadata:                        Unparsed line from the PC-Wetterstation data file containing the
                                                metadata
        :type metadata:                         string
        :param station_id:                      ID of the current weather station being processed
        :type station_id:                       string
        :return:                                parsed metadata of the station, reference value of the rain counter at
                                                the beginning of the data file (in mm)
        :rtype:                                 tuple(WeatherStationMetadata, float)
        :raise PCWetterstationFileParseError:   if the metadata could not be parsed
        """
        device_info = ""
        location_info = ""
        station_height = float('NaN')
        rain_calib_factor = float('NaN')
        rain_counter_base = float('NaN')
        latitude = float('NaN')
        longitude = float('NaN')

        try:
            # parse header lines
            splitted_line = str.split(metadata, '#')
            for line in splitted_line:
                line_pair = str.split(line, '=')
                if line_pair[0] == 'Calibrate':
                    rain_calib_factor = float(line_pair[1])
                elif line_pair[0] == 'Regen0':
                    line_pair[1].index('mm')  # will raise an exception if the format is wrong
                    rain_counter_base = float(line_pair[1].replace('mm', ''))
                elif line_pair[0] == 'Location':
                    location_pair = str.split(line_pair[1], '/')
                    if '(' and ')' in location_pair[0]:
                        # if something with brackets is present, this is assumed to contain coordinates
                        geographical_location_pair = str.split(extract_bracket_contents(location_pair[0]), ',')
                        latitude = float(geographical_location_pair[0].replace('\N{DEGREE SIGN}', ''))
                        longitude = float(geographical_location_pair[1].replace('\N{DEGREE SIGN}', ''))
                        location_info = str.strip(str.split(location_pair[0], '(')[0])
                    else:
                        # default behaviour
                        location_info = location_pair[0]
                    location_pair[1].index('m')  # will raise an exception if the format is wrong
                    station_height = int(location_pair[1].replace('m', ''))
                elif line_pair[0] == 'Station':
                    if '(' and ')' in line_pair[1]:
                        # if something within brackets is present, this is assumed to contain the device info
                        device_info = extract_bracket_contents(line_pair[1])
                    else:
                        # default behaviour
                        device_info = line_pair[1]

            station_metadata = WeatherStationMetadata(station_id, device_info, location_info, latitude, longitude,
                                                      station_height, rain_calib_factor)
        except Exception as e:
            raise PCWetterstationFileParseError("File header parsing error: %s" % str(e))

        return station_metadata, rain_counter_base

    def write(self, file_path, data, station_metadata):
        """
        Writes a PC-Wetterstation format data file. For each month a single file is written
        (following the file format standard)

        :param file_path:                       path where the data file will be written to
        :type file_path:                        string
        :param data:                            weather data written to the file. It is expected to be sorted by
                                                ascending time.
        :type data:                             list of WeatherStationDataset
        :param station_metadata:                metadata of the station
        :type station_metadata:                 WeatherStationMetadata
        :raise DatasetFormatError:              if a required sensor is missing in the data
         """
        # generate settings line for the CSV-file
        metadata_line = self._create_settings_header_line(station_metadata)

        dataset_index = 0
        while dataset_index < len(data):
            # generate file name based on the first dataset
            first_date = data[dataset_index].get_time()
            file_name = PCWetterstationFormatFile._DATA_FILE_TAG + first_date.strftime('%m_%y') + '.csv'
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
                        f.write(metadata_line + '\r\n')
                        writer.writerow(sensor_list)
                        is_first = False

                    writer.writerow(values)
                    dataset_index += 1

    @staticmethod
    def _in_same_month(first_date, second_date):
        """
        Determines if the two dates are within the same month.

        :param first_date:                      first date to be compared
        :type first_date:                       datetime.datetime
        :param second_date:                     second date to be compared
        :type second_date:                      datetime.datetime
        :return:                                True if both dates are within the same month, False otherwise
        :rtype:                                 boolean
        """
        if first_date.month == second_date.month and first_date.year == second_date.year:
            return True
        else:
            return False

    @staticmethod
    def _create_settings_header_line(station_metadata):
        """
        Helper method for creating the settings header line of a PC-Wetterstation format file.

        :param station_metadata:                station metadata to be written to a PC-Wetterstation station header line
        :type station_metadata:                 WeatherStationMetadata
        :return:                                header line for the PC-Wetterstation file format
        :rtype:                                 string
        """
        station_id = station_metadata.get_station_id()
        location = station_metadata.get_location_info()
        station_latitude, station_longitude, station_height = station_metadata.get_geo_info()
        device_info = station_metadata.get_device_info()
        rain_calib_factor = station_metadata.get_rain_calib_factor()

        settings_line = '#Calibrate=' + str('%1.3f' % rain_calib_factor) + ' #Regen0=0mm #Location=' + \
                        str(location) + ' (' + str(station_latitude) + '\N{DEGREE SIGN}, ' + \
                        str(station_longitude) + '\N{DEGREE SIGN}) ' + '/ ' + str(int(station_height)) + \
                        'm #Station=' + str(station_id) + " (" + device_info + ")"

        return settings_line

    @staticmethod
    def _date_to_str(date):
        """
        Performance efficient converting of a date object to a string.

        :param date:                            date to be converted
        :type date:                             date
        :return:                                date in the format DD.MM.YYYY
        :rtype:                                 string
        """
        year, month, day = str(date).split('-')
        return day + '.' + month + '.' + year

    @staticmethod
    def _time_to_str(time):
        """
        Performance efficient converting of a time object to a string.

        :param time:                            time to be converted
        :type time:                             time
        :return:                                time in the format HH:MM
        :rtype:                                 string
        """
        return str(time)[0:-3]  # removes the seconds

    def _get_line(self, dataset):
        """
        Helper method for preparing a single data line to be written into a PC-Wetterstation format file.
        Also returns header lines describing the sensors.

        :param dataset:                         dataset to be converted into a PC-Wetterstation file data line
        :type dataset:                          WeatherStationDataset object
        :return:                                data line for the PC-Wetterstation file format, header line for the
                                                sensor descriptions, units and (PC-Wetterstation internal) sensor IDs
        :rtype:                                 tuple(list of floats, list of strings, list of strings, list of int)
        :raise DatasetFormatError:              if a required sensor is missing in the data
        """
        values = []
        sensor_list = []
        description_list = []
        unit_list = []

        # read the date and time
        time = dataset.get_time()
        values.append(self._date_to_str(time.date()))
        sensor_list.append("")
        description_list.append(PCWetterstationFormatFile._DATE)
        unit_list.append("")

        values.append(self._time_to_str(time.time()))
        sensor_list.append("")
        description_list.append(PCWetterstationFormatFile._TIME)
        unit_list.append("")

        # read all sensor data
        for required_sensor, sensor_format_specific_ID in self._sensor_list.items():
            try:
                values.append(dataset.get_sensor_value(required_sensor))
                description_list.append(dataset.get_sensor_description(required_sensor))
                unit_list.append(dataset.get_sensor_unit(required_sensor))
                sensor_list.append(sensor_format_specific_ID)
            except:
                raise DatasetFormatError(
                    "Sensor %s is missing in the data to be written to file" % str(required_sensor))

        return values, description_list, unit_list, sensor_list