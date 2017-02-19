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

import datetime
import sqlite3

from remote_weather_access.common.datastructures import WeatherStationDataset
from remote_weather_access.common.logging import MultiProcessLoggerProxy
from remote_weather_access.server._sqldatabase_impl import _WeatherStationTable, _WindSensorTable, _RainSensorTable, \
    _CombiSensorDataTable, _WeatherDataTable, _CombiSensorDefinitionTable
from remote_weather_access.server.interface import IDatabaseService, IDatabaseServiceFactory


class SQLDatabaseService(IDatabaseService):
    """SQL weather database service serving as a facade"""
    def __init__(self, db_file_name, logging_connection=None):
        """
        Constructor.

        :param db_file_name:            name and path of the SQLite-database file
        :type db_file_name:             string
        :param logging_connection:      connection to the main process logger, may be omitted if no logging is required
        :type logging_connection:       common.logging.MultiProcessConnector
        """
        if logging_connection:
            self._logger = MultiProcessLoggerProxy(logging_connection)
        else:
            self._logger = None
        self._observers = []
        self._database = SQLWeatherDB(db_file_name)

    def add_data(self, message):
        """
        Adds a dataset to the database.
        Note: Logging is only supported if the method is called from another than the main process.
        If already data exists for the requested station and timepoint, it is replaced silently if this operation
        is unambiguous.

        :param message:                 weather data message to be stored
        :type message:                  common.datastructures.WeatherMessage
        :raise NotExistingError:        if a requested station or sensor ID is not existing in the database
        :raise AlreadyExistingError:    if a dataset is already existing in the database for the given station,
                                        time or sensor ID and the replacement would be ambiguous, in that case the
                                        database remains unchanged
        """
        data = message.get_data()
        station_id = message.get_station_id()
        message_id = message.get_message_id()

        # concurrent calls to the database are allowed
        self._database.add_dataset(station_id, data)

        # trigger acknowledgment to the client
        self._notify_observers(message_id)

    def get_combi_sensors(self):
        """
        Obtains the sensor IDs of the combi sensors present in the database.

        :return:                        sensor IDs, descriptions of all combi sensors in the database
        :rtype:                         tuple(list of string, dict(string, string))
        """
        return self._database.get_combi_sensors()

    def register_observer(self, observer):
        """
        Registers a new observer.

        :param observer:                observer object to be registered
        :type observer:                 server.interface.IServerSideProxy
        """
        self._observers.append(observer)

    def unregister_observer(self, observer):
        """
        Unregisters an observer.

        :param observer:                observer object to be removed
        :type observer:                 server.interface.IServerSideProxy
        """
        self._observers.remove(observer)

    def _notify_observers(self, finished_id):
        """
        Notify all observers about the finished storage of a database

        :param finished_id:             ID of the processed message
        :type finished_id:              string
        """
        if self._logger:
            # we will come here only on a subprocess
            for observer in self._observers:
                observer.acknowledge_persistence(finished_id, self._logger)


class SQLDatabaseServiceFactory(IDatabaseServiceFactory):
    """Factory for weather database services"""
    def __init__(self, db_file_name, logging_connection=None):
        """
        Constructor.

        :param db_file_name:            name and path of the SQLite-database file
        :type db_file_name:             string
        :param logging_connection:      connection to the main process logger, may be omitted if no logging is required
        :type logging_connection:       common.logging.MultiProcessConnector
        """
        self._db_file_name = db_file_name
        self._logging_connection = logging_connection

    def create(self, use_logging):
        """
        Creates a class instance.
        Note: If that instance is created with an active logger connection, it must not be executed on the main process.

        :param use_logging:             Flag stating if that instance should contain a connection to the main logger
        :type use_logging:              bool
        :return:                        new class instance
        :rtype:                         SQLDatabaseService
        """
        if use_logging:
            sql_database_service = SQLDatabaseService(self._db_file_name, self._logging_connection)
        else:
            sql_database_service = SQLDatabaseService(self._db_file_name)
        return sql_database_service


class SQLWeatherDB(object):
    """
    Persistent weather SQL-database.
    SQLlite can handle concurrency, i.e. multiple concurrent objects of the class are allowed at any time.
    """
    def __init__(self, db_file):
        """
        Constructor.

        :param db_file:             name and path of the SQLite-database file
        :type db_file:              string
        """
        # open the database
        self._sql = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self._sql.row_factory = sqlite3.Row

        # create the SQL tables if required
        with self._sql:
            self._weather_station_table = _WeatherStationTable(self._sql)
            self._base_station_data_table = _WeatherDataTable(self._sql)
            self._wind_sensor_table = _WindSensorTable(self._sql)
            self._combi_sensor_data_table = _CombiSensorDataTable(self._sql)
            self._combi_sensor_definition_table = _CombiSensorDefinitionTable(self._sql)
            self._rain_sensor_table = _RainSensorTable(self._sql)

            self._sql.execute("PRAGMA foreign_keys = ON")

    def close_database(self):
        """
        Dispose method used for guaranteed closing of the database connection.
        """
        self._sql.close()

    def add_dataset(self, station_id, data):
        """
        Adds a new dataset to the database.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.
        If already data exists for the requested station and timepoint, it is replaced silently if this operation
        is unambiguous.

        :param station_id:              station ID
        :type station_id:               string
        :param data:                    data for (possibly several) timepoints
        :type data:                     list of common.datastructures.WeatherStationDataset
        :raise NotExistingError:        if a requested station or sensor ID is not existing in the database
        :raise AlreadyExistingError:    if a dataset is already existing in the database for the given station,
                                        time or sensor ID and the replacement would be ambiguous, in that case the
                                        database remains unchanged
        """
        if not isinstance(data, list):
            data = [data]

        with self._sql:
            # add the dataset to the database
            self._base_station_data_table.add(station_id, data)

            # from here it is guaranteed that a dataset for the given station and time exists in the database
            self._rain_sensor_table.add(station_id, data)
            self._wind_sensor_table.add(station_id, data)
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()
            self._combi_sensor_data_table.add(
                station_id, available_combi_sensor_ids, combi_sensor_descriptions, data
            )  # temperature / humidity

    def replace_dataset(self, station_id, data):
        """
        Replaces an existing dataset. For each station, timepoint and sensor ID already data needs to exist.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.

        :param station_id:          station ID
        :type station_id:           string
        :param data:                data for (possibly several) timepoints
        :type data:                 list of common.datastructures.WeatherStationDataset
        :raise NotExistingError:    if no entry exists for the requested station and timepoint or sensor ID
        """
        if not isinstance(data, list):
            data = [data]

        with self._sql:
            available_combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            for dataset in data:
                # replace the dataset
                self._base_station_data_table.replace(station_id, dataset)
                self._rain_sensor_table.replace(station_id, dataset)
                self._wind_sensor_table.replace(station_id, dataset)
                combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()
                self._combi_sensor_data_table.replace(station_id, dataset, available_combi_sensor_ids,
                                                      combi_sensor_descriptions)  # temperature / humidity

    def remove_dataset(self, station_id, time):
        """
        Deletes the given dataset. UNDO is NOT possible.

        :param station_id:          station ID
        :type station_id:           string
        :param time:                timepoint(s). Multiple times can be deleted at once.
        :type time:                 list of datetime.datetime
        :return:                    number of deleted datasets
        :rtype:                     integer
        """
        # all cascaded data is also automatically deleted
        num_deleted_rows = self._base_station_data_table.remove(station_id, time)

        return num_deleted_rows

    def get_data_in_time_range(self, station_id, first_time, last_time):
        """
        Returns all datasets for the given station within the given time range.

        :param station_id:          station ID
        :type station_id:           string
        :param first_time:          beginning of the requested time range (inclusive)
        :type first_time:           datetime.datetime
        :param last_time:           end of the requested time range (inclusive)
        :type last_time:            datetime.datetime
        :return:                    weather datasets for the requested timepoints, sorted by ascending time. If no data
                                    exists for the requested range, it is empty.
        :rtype:                     list of common.datastructures.WeatherStationDataset
        """
        with self._sql:
            times_in_range, base_data_in_range = \
                self._base_station_data_table.get_data(station_id, first_time, last_time)
            rain_in_range = self._rain_sensor_table.get_data(station_id, first_time, last_time)
            wind_in_range = self._wind_sensor_table.get_data(station_id, first_time, last_time)
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

            # iterate over all times in the time range in order
            datasets = []
            for time, base, rain, wind in zip(times_in_range, base_data_in_range, rain_in_range, wind_in_range):
                combi_data_from_db = self._combi_sensor_data_table.get_data_at_time(
                    station_id, time, combi_sensor_descriptions
                )

                # create the dataset
                curr_dataset = WeatherStationDataset(time)
                for sensor_data in combi_data_from_db:
                    curr_dataset.add_sensor(sensor_data)
                curr_dataset.add_sensor(base)
                curr_dataset.add_sensor(rain)
                curr_dataset.add_sensor(wind)

                datasets.append(curr_dataset)

        return datasets

    def add_station(self, station):
        """
        Adds a new weather station to the database.

        :param station:                 metadata of the station
        :type station:                  common.datastructures.WeatherStationMetadata
        :raise AlreadyExistingError:    if the station is already existing in the database
        """
        with self._sql:
            self._weather_station_table.add(station)

    def replace_station(self, station):
        """
        Replaces the metadata of an existing weather station in the database. DO NOT USE this method if a station
        has been relocated to a new place. Create instead a new station with a new identifier.

        :param station:                 metadata of the station
        :type station:                  common.datastructures.WeatherStationMetadata
        :raise NotExistingError:        if the station is not existing in the database
        """
        with self._sql:
            self._weather_station_table.replace(station)

    def remove_station(self, station_id):
        """
        Removes an existing station from the database. All weather data entries are also deleted.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        success flag of the remove operation (true: removal was successful,
                                        false: otherwise)
        :rtype:                         boolean
        """
        with self._sql:
            is_successful = self._weather_station_table.remove(station_id)

        return is_successful

    def station_exists(self, station_id):
        """
        Checks if a station exists in the database.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        True if the station exists in the database, false otherwise
        :rtype:                         boolean
        """
        with self._sql:
            does_exist = self._weather_station_table.exists(station_id)

        return does_exist

    def get_station_metadata(self, station_id):
        """
        Obtains the metadata for a station from the database.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        metadata of the station
        :rtype:                         common.datastructures.WeatherStationMetadata
        """
        with self._sql:
            station_metadata = self._weather_station_table.get_metadata(station_id)

        return station_metadata

    def get_stations(self):
        """
        Obtains all stations registered in the database.

        :return:                        list of the IDs of all stations registered in the database
        :rtype:                         list of string
        """
        with self._sql:
            station_ids = self._weather_station_table.get_stations()

        return station_ids

    def add_combi_sensor(self, sensor_id, description):
        """
        Adds a combi sensor (temperature + humidity). If it already exists in the database, nothing is changed.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :param description:             description text of the sensor (location, type, specialities, ...)
        :type description:              string
        :raise AlreadyExistingError:    if the sensor ID already exists in the database
        """
        with self._sql:
            self._combi_sensor_definition_table.add(sensor_id, description)

    def replace_combi_sensor(self, sensor_id, description):
        """
        Replaces an existing combi sensor description without changing the data.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :param description:             description of the sensor (location, type, specialities, ...)
        :type description:              string
        :raise NotExistingError:        if the combi sensor ID does not exist in the database
        """
        with self._sql:
            self._combi_sensor_definition_table.replace(sensor_id, description)

    def combi_sensor_exists(self, sensor_id):
        """
        Checks if a combi sensor exists in the database.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :return:                        True if the combi sensor exists in the database, false otherwise
        :rtype:                         boolean
        """
        with self._sql:
            is_existing = self._combi_sensor_definition_table.exists(sensor_id)

        return is_existing

    def get_combi_sensors(self):
        """
        Obtains all combi sensors registered in the database.

        :return:                        sensor IDs, descriptions of all combi sensors in the database
        :rtype:                         tuple(list of string, dict(string, string))
        """
        with self._sql:
            combi_sensor_ids = self._combi_sensor_definition_table.get_combi_sensor_ids()
            combi_sensor_descriptions = self._combi_sensor_definition_table.get_sensor_descriptions()

        return combi_sensor_ids, combi_sensor_descriptions

    def remove_combi_sensor(self, sensor_id):
        """
        Removes an existing combi sensor from the database.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :return:                        success of the delete operation
        :rtype:                         boolean
        """
        with self._sql:
            is_deleted = self._combi_sensor_definition_table.remove(sensor_id)

        return is_deleted
