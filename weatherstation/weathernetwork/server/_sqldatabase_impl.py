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

import sqlite3

from weathernetwork.common import utilities
from weathernetwork.common.datastructures import WeatherStationMetadata, WindSensorData, RainSensorData, \
    CombiSensorData, BaseStationSensorData
from weathernetwork.server.exceptions import AlreadyExistingError, NotExistingError


class _WeatherStationTable(object):
    """
    Representing the table 'WeatherStation' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
        CREATE TABLE IF NOT EXISTS WeatherStation \
            ( \
                stationID VARCHAR(10) NOT NULL PRIMARY KEY, \
                device VARCHAR(255) NOT NULL, \
                location VARCHAR(255) NOT NULL, \
                latitude REAL NOT NULL, \
                longitude REAL NOT NULL, \
                height REAL NOT NULL, \
                rainCalibFactor REAL NOT NULL \
            )")

    def add(self, station):
        """
        Adds a new weather station to the database.

        :param station:                 metadata of the station
        :type station:                  common.datastructures.WeatherStationMetadata
        :raise AlreadyExistingError:    if the station is already existing in the database
        """
        identifier = station.get_station_id()
        device = station.get_device_info()
        location = station.get_location_info()
        latitude, longitude, height = station.get_geo_info()
        rain_calib_factor = station.get_rain_calib_factor()

        try:
            self._sql.execute(" \
                INSERT INTO WeatherStation ( \
                    stationID, \
                    device, \
                    location, \
                    latitude, \
                    longitude, \
                    height, \
                    rainCalibFactor) VALUES (?,?,?,?,?,?,?)",
                              (identifier, device, location, latitude, longitude, height, rain_calib_factor))
        except sqlite3.Error:
            raise AlreadyExistingError("The station is already existing")

    def replace(self, station):
        """
        Replaces the metadata of an existing weather station in the database. DO NOT USE this method if a station
        has been relocated to a new place. Create instead a new station with a new identifier.

        :param station:                 metadata of the station
        :type station:                  common.datastructures.WeatherStationMetadata
        :raise NotExistingError:        if the station is not existing in the database
        """
        identifier = station.get_station_id()
        device = station.get_device_info()
        location = station.get_location_info()
        latitude, longitude, height = station.get_geo_info()
        rain_calib_factor = station.get_rain_calib_factor()

        num_updated_rows = self._sql.execute(" \
            UPDATE WeatherStation \
            SET device=(?), location=(?), latitude=(?), longitude=(?), height=(?), rainCalibFactor=(?) \
            WHERE stationID=(?) ",
                                             (device, location, latitude, longitude, height, rain_calib_factor,
                                              identifier)).rowcount

        if num_updated_rows == 0:
            raise NotExistingError("The station is not existing")

    def remove(self, station_id):
        """
        Removes an existing station from the database. All weather data entries are also deleted.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        success flag of the remove operation (true: removal was successful,
                                        false: otherwise)
        :rtype:                         boolean
        """
        num_deleted_rows = self._sql.execute(" \
            DELETE \
            FROM WeatherStation \
            WHERE stationID=(?)",
                                             (station_id,)).rowcount

        if num_deleted_rows == 1:
            return True
        else:
            return False

    def exists(self, station_id):
        """
        Checks if a station exists in the database.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        True if the station exists in the database, false otherwise
        :rtype:                         boolean
        """
        is_existing = self._sql.execute(" \
            SELECT EXISTS ( \
                SELECT * \
                FROM WeatherStation \
                WHERE stationID=(?) \
            )", (station_id,)).fetchone()[0]

        return is_existing

    def get_metadata(self, station_id):
        """
        Obtains the metadata for a station from the database.

        :param station_id:              station ID
        :type station_id:               string
        :return:                        metadata of the station
        :rtype:                         common.datastructures.WeatherStationMetadata
        :raise NotExistingError:        if the requested station ID is not existing in the database
        """
        station_metadata_line = self._sql.execute(" \
            SELECT * \
            FROM WeatherStation \
            WHERE stationID=(?)", (station_id,)).fetchone()

        if not station_metadata_line:
            raise NotExistingError("The requested station ID is not existing in the database")

        metadata = dict(station_metadata_line)
        station_metadata = WeatherStationMetadata(metadata["stationID"], metadata["device"],
                                                  metadata["location"],
                                                  metadata["latitude"], metadata["longitude"],
                                                  metadata["height"],
                                                  metadata["rainCalibFactor"])

        return station_metadata


class _WindSensorTable(object):
    """
    Representing the table 'WindSensorData' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
            CREATE TABLE IF NOT EXISTS WindSensorData \
            ( \
                stationID VARCHAR(10) NOT NULL, \
                time TIMESTAMP NOT NULL, \
                direction REAL, \
                speed REAL, \
                gusts REAL, \
                temperature REAL, \
                FOREIGN KEY(stationID, time) \
                    REFERENCES WeatherData(stationID, time) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE, \
                PRIMARY KEY(stationID, time) \
            )")

    def add(self, station_id, data):
        """
        Adds a a new dataset to the database table.

        :param station_id:              station ID
        :type station_id:               string
        :param data:                    datasets to be added to the database table
        :type data:                     list of common.datastructures.WeatherStationDataset
        """
        data_to_be_written = []
        for dataset in data:
            time = dataset.get_time()
            wind_average, wind_gust, wind_direction, wind_chill_temp = dataset.get_sensor_object(
                WindSensorData.WIND).get_all_data()
            data_to_be_written.append((time, station_id, wind_direction, wind_average, wind_gust, wind_chill_temp))

        self._sql.executemany(" \
            INSERT INTO WindSensorData ( \
                time, \
                stationID, \
                direction, \
                speed, \
                gusts, \
                temperature \
            ) VALUES (?,?,?,?,?,?)",
                              data_to_be_written)

    def replace(self, station_id, dataset):
        """
        Replaces the dataset in the database table.

        :param station_id:              station ID for which the dataset should be replaced
        :type station_id:               string
        :param dataset:                 new dataset
        :type dataset:                  common.datastructures.WeatherStationDataset
        """
        time = dataset.get_time()
        wind_average, wind_gust, wind_direction, wind_chill_temp = dataset.get_sensor_object(
            WindSensorData.WIND).get_all_data()
        self._sql.execute(" \
            UPDATE WindSensorData \
            SET direction=(?), speed=(?), gusts=(?), temperature=(?) \
            WHERE time=(?) AND stationID=(?)",
                          (wind_direction, wind_average, wind_gust, wind_chill_temp, time, station_id))

    def get_data(self, station_id, first_time, last_time):
        """
        Obtains the data in the table for a certain time interval.

        :param station_id:              station ID for which the data is required
        :type station_id:               string
        :param first_time:              beginning of the time interval (inclusive)
        :type first_time:               datetime.datetime
        :param last_time:               end of the time interval (inclusive)
        :type last_time:                datetime.datetime
        :return:                        wind sensor data for all timepoints within the interval
        :rtype:                         list of common.datastructures.WindSensorData
        """
        wind_data_from_db = self._sql.execute(" \
            SELECT speed, gusts, direction, temperature \
            FROM WindSensorData \
            WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
            ORDER BY time",
                                              (station_id, first_time, last_time)).fetchall()

        wind_data = []
        for wind_data_for_timepoint in wind_data_from_db:  # type: dict
            wind_data.append(WindSensorData(wind_data_for_timepoint["speed"],
                                            wind_data_for_timepoint["gusts"],
                                            wind_data_for_timepoint["direction"],
                                            wind_data_for_timepoint["temperature"])
                             )
        return wind_data


class _RainSensorTable(object):
    """
    Representing the table '_RainSensorTable' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
            CREATE TABLE IF NOT EXISTS RainSensorData \
            ( \
                stationID VARCHAR(10) NOT NULL, \
                beginTime TIMESTAMP NOT NULL, \
                endTime TIMESTAMP NOT NULL, \
                amount REAL, \
                FOREIGN KEY(stationID, endTime) \
                    REFERENCES WeatherData(stationID, time) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE, \
                PRIMARY KEY (stationID, endTime), \
                CHECK(endTime>beginTime) \
            )")

    def add(self, station_id, data):
        """
        Adds a new rain sensor data to the database table.
        If cumulated rain amount is present in the data, it is ignored.

        :param station_id:              station ID
        :type station_id:               string
        :param data:                    datasets to be added to the table
        :type data:                     list of common.datastructures.WeatherStationDataset
        :raise AlreadyExistingError:    if a rain sensor dataset already exists for the given time
        :raise ValueError:              if the begin time of the rain sensor interval is the same as or later than
                                        the end time
        """
        # obtain the base station data
        data_to_be_written = []
        time_intervals = []
        for dataset in data:
            time = dataset.get_time()
            amount, begin_time, *rest = dataset.get_sensor_object(RainSensorData.RAIN).get_all_data()
            time_intervals.append((begin_time, time))
            data_to_be_written.append((time, station_id, amount, begin_time))

        # ensure the uniqueness of the rain sensor intervals
        for begin_time, end_time in utilities.consolidate_ranges(time_intervals):
            if self._rain_sensor_period_exists(station_id, begin_time, end_time):
                raise AlreadyExistingError("For the given station (%s), a rain sensor dataset within the given time "
                                           "interval (%s - %s) already exists in the database"
                                           % (station_id, str(begin_time), str(end_time)))

        try:
            self._sql.executemany(" \
                INSERT INTO RainSensorData ( \
                    endTime, \
                    stationID, \
                    amount, \
                    beginTime \
                ) VALUES (?,?,?,?)",
                                  data_to_be_written)
        except sqlite3.Error as e:
            if "CONSTRAINT FAILED" in e.args[0].upper():
                raise ValueError(
                    "The begin time of the rain sensor interval is the same as or later than the end time")
            else:
                raise

    def replace(self, station_id, dataset):
        """
        Replaces an existing dataset in the database table.
        Note: Cumulated rain amounts are not stored in the database.

        :param station_id:          station ID for which the dataset should be replaced
        :type station_id:           string
        :param dataset:             new dataset
        :type dataset:              common.datastructures.WeatherStationDataset
        :raise NotExistingError:    if the begin time of the rain sensor data cannot be updated
        """
        time = dataset.get_time()
        amount, begin_time, *rest = dataset.get_sensor_object(RainSensorData.RAIN).get_all_data()
        num_updated_rows = self._sql.execute(" \
            UPDATE RainSensorData \
            SET amount=(?) \
            WHERE endTime=(?) AND beginTime=(?) AND stationID=(?)",
                                             (amount, time, begin_time, station_id)).rowcount

        if num_updated_rows == 0:
            raise NotExistingError("The rain amount cannot be updated.")

    def _rain_sensor_period_exists(self, station_id, first_time, last_time):
        """
        Determines if rain sensor data for the specified time interval already exists.

        :param station_id:          station ID
        :type station_id:           string
        :param first_time:          begin time of the interval (inclusive)
        :type first_time:           datetime.datetime
        :param last_time:           end time of the interval (inclusive)
        :type last_time:            datetime.datetime
        :return:                    True if rain sensor data exists, false otherwise
        :rtype:                     boolean
        """
        is_existing = self._sql.execute(" \
            SELECT EXISTS( \
                SELECT * \
                FROM   RainSensorData \
                WHERE  stationID=(?) AND (?)<endTime AND beginTime<(?) \
            )", (station_id, first_time, last_time)).fetchone()[0]

        return is_existing

    def get_data(self, station_id, first_time, last_time):
        """
        Obtains the rain sensor data for the specified period from the database table.

        :param station_id:          station ID
        :type station_id:           string
        :param first_time:          first end time of the interval (inclusive)
        :type first_time:           datetime.datetime
        :param last_time:           last end time of the interval (inclusive)
        :type last_time:            datetime.datetime
        :return:                    rain sensor data within the specified interval
        :rtype:                     list of common.datastructures.RainSensorData
        """
        rain_data_from_db = self._sql.execute(" \
            SELECT amount, beginTime, endTime \
            FROM RainSensorData \
            WHERE stationID=(?) AND endTime BETWEEN (?) AND (?) \
            ORDER BY endTime",
                                              (station_id, first_time, last_time)).fetchall()

        rain_data = []
        cumulated_rain = 0
        is_first = True
        for rain_data_for_timepoint in rain_data_from_db:  # type: dict
            end_time = rain_data_for_timepoint["endTime"]
            if is_first:
                first_time_with_data = end_time  # only the rain fallen from the first end time is taken into account

            # create the dataset (the database does not store cumulated amounts)
            amount = rain_data_for_timepoint["amount"]
            if not is_first:
                cumulated_rain += amount  # the cumulated rain sum starts always with 0
            rain_data.append(RainSensorData(
                amount,
                rain_data_for_timepoint["beginTime"],
                cumulated_rain,
                first_time_with_data)
            )

            is_first = False

        return rain_data


class _CombiSensorDataTable(object):
    """
    Representing the table 'CombiSensorData' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
            CREATE TABLE IF NOT EXISTS CombiSensorData \
            ( \
                stationID VARCHAR(10) NOT NULL, \
                time TIMESTAMP NOT NULL, \
                sensorID VARCHAR(10) NOT NULL, \
                temperature REAL, \
                humidity REAL, \
                FOREIGN KEY(stationID, time) \
                    REFERENCES WeatherData(stationID, time) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE, \
                FOREIGN KEY(sensorID) \
                    REFERENCES CombiSensor(sensorID) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE, \
                PRIMARY KEY(stationID, time, sensorID) \
            )")

    def add(self, station_id, available_combi_sensor_ids, combi_sensor_descriptions, data):
        """
        Adds a new dataset to the database table.

        :param station_id:                      station ID
        :type station_id:                       string
        :param available_combi_sensor_ids:      list of all available combi sensor IDs
        :type available_combi_sensor_ids:       list of string
        :param combi_sensor_descriptions:       descriptions of all available combi sensors
        :type combi_sensor_descriptions:        dict(string, string)
        :param data:                            dataset to be added
        :type data:                             list of common.datastructures.WeatherStationDataset
        :raise NotExistingError:                if a required component does not exist (for example: combi sensor)
        """
        for sensor_ID in available_combi_sensor_ids:
            data_to_be_written = []
            for dataset in data:
                if dataset.contains(sensor_ID):
                    time = dataset.get_time()
                    temperature, humidity = dataset.get_sensor_object(sensor_ID).get_all_data()
                    combi_sensor_description = dataset.get_sensor_object(sensor_ID).get_combi_sensor_description()
                    if combi_sensor_description:
                        if combi_sensor_descriptions[sensor_ID] != combi_sensor_description:
                            raise NotExistingError(
                                "The combi sensor description of the new data differs from that stored in the database."
                            )

                    data_to_be_written.append((time, station_id, sensor_ID, temperature, humidity))

            if data_to_be_written:
                try:
                    self._sql.executemany(" \
                        INSERT INTO CombiSensorData ( \
                            time, \
                            stationID, \
                            sensorID, \
                            temperature, \
                            humidity \
                        ) VALUES (?,?,(SELECT sensorID from CombiSensor WHERE sensorID=(?)),?,?)",
                                          data_to_be_written)
                except sqlite3.Error as e:
                    if "NULL" in e.args[0].upper():
                        raise NotExistingError("The combi sensor ID does not exist in the database")
                    else:
                        raise

    def replace(self, station_id, dataset, available_combi_sensor_ids, combi_sensor_descriptions):
        """
        Replaces a dataset in the database table.

        :param station_id:                      station ID
        :type station_id:                       string
        :param dataset:                         new dataset
        :type dataset:                          common.datastructures.WeatherStationDataset
        :param available_combi_sensor_ids:      list of all available combi sensor IDs
        :type available_combi_sensor_ids:       list of string
        :param combi_sensor_descriptions:       descriptions of all available combi sensors
        :type combi_sensor_descriptions:        dict(string, string)
        :raise NotExistingError:                if a required component does not exist (for example: station ID)
        """
        time = dataset.get_time()
        for sensor_ID in available_combi_sensor_ids:
            if dataset.contains(sensor_ID):
                temperature, humidity = dataset.get_sensor_object(sensor_ID).get_all_data()
                combi_sensor_description = dataset.get_sensor_object(sensor_ID).get_combi_sensor_description()
                if combi_sensor_description:
                    if combi_sensor_descriptions[sensor_ID] != combi_sensor_description:
                        raise NotExistingError(
                            "The combi sensor description of the new data differs from that stored in the database."
                        )

                num_updated_rows = self._sql.execute(" \
                    UPDATE CombiSensorData \
                    SET temperature=(?), humidity=(?) \
                    WHERE time=(?) AND stationID=(?) AND sensorID=(?)",
                                                     (temperature, humidity, time, station_id,
                                                      sensor_ID)).rowcount

                if num_updated_rows == 0:
                    raise NotExistingError("The requested combination of time, station ID and sensor ID does not exist")

    def get_data_at_time(self, station_id, time, combi_sensor_descriptions):
        """
        Obtains the combi sensor data for the specified timepoint from the database.

        :param station_id:                      station ID
        :type station_id:                       string
        :param time:                            timepoint for which the data is requested
        :type time:                             datetime.datetime
        :param combi_sensor_descriptions:       list of the descriptions of all available combi sensors
        :type combi_sensor_descriptions:        list of string
        :return:                                combi sensor data for the time point
        :rtype:                                 list of common.datastructures.CombiSensorData
        """
        combi_data_from_db = self._sql.execute(" \
                SELECT temperature, humidity, sensorID \
                FROM CombiSensorData \
                WHERE stationID=(?) AND time=(?) \
                ORDER BY sensorID",
                                               (station_id, time)).fetchall()

        combi_data = []
        for sensor_data in combi_data_from_db:  # type: dict
            sensor_id = sensor_data["sensorID"]
            combi_data.append(CombiSensorData(
                sensor_id,
                sensor_data["temperature"],
                sensor_data["humidity"],
                combi_sensor_descriptions[sensor_id])
            )

        return combi_data


class _WeatherDataTable(object):
    """
    Representing the table 'WeatherDataTable' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
            CREATE TABLE IF NOT EXISTS WeatherData \
            ( \
                stationID VARCHAR(10) NOT NULL, \
                time TIMESTAMP NOT NULL, \
                pressure REAL, \
                UV REAL, \
                FOREIGN KEY(stationID) \
                    REFERENCES WeatherStation(stationID) \
                    ON DELETE CASCADE \
                    ON UPDATE CASCADE, \
                PRIMARY KEY(stationID, time) \
            )")

    def add(self, station_id, data):
        """
        Adds new datasets to the table in the database, existing datasets are replaced.

        :param station_id:              station ID
        :type station_id:               string
        :param data:                    datasets to be added to the table
        :type data:                     list of common.datastructures.WeatherStationDataset
        :raise NotExistingError:        if the requested station does not exist in the database
        """
        # obtain the base station data
        data_to_be_written = []
        for dataset in data:
            time = dataset.get_time()
            pressure, uv = dataset.get_sensor_object(BaseStationSensorData.BASE_STATION).get_all_data()
            data_to_be_written.append((time, station_id, pressure, uv))

        if data_to_be_written:
            try:
                # if a dataset exists, it will be replaced and all referenced datasets will be deleted
                self._sql.executemany(" \
                    REPLACE INTO WeatherData ( \
                        time, \
                        stationID, \
                        pressure, \
                        UV \
                    ) VALUES (?,(SELECT stationID from WeatherStation WHERE stationID=(?)),?,?)",
                                      data_to_be_written)
            except sqlite3.Error as e:
                if "NULL" in e.args[0].upper():
                    raise NotExistingError("The station does not exist in the database")
                else:
                    raise

    def replace(self, station_id, dataset):
        """
        Replaces a dataset in the table in the database.

        :param station_id:              station ID
        :type station_id:               string
        :param dataset:                 new dataset
        :type dataset:                  common.datastructures.WeatherStationDataset
        :raise NotExistingError:        if no entry for the given time and station exists in the database
        """
        time = dataset.get_time()
        pressure, uv = dataset.get_sensor_object(BaseStationSensorData.BASE_STATION).get_all_data()
        num_updated_rows = self._sql.execute(" \
            UPDATE WeatherData \
            SET pressure=(?), UV=(?) \
            WHERE time=(?) AND stationID=(?)",
                                             (pressure, uv, time, station_id)).rowcount

        if num_updated_rows == 0:
            raise NotExistingError("No entry exists for the requested station at the requested time")

    def remove(self, station_id, time):
        """
        Deletes the given dataset(s) from the table in the database. UNDO is NOT possible.
        All cascaded data from other tables in the database is also automatically removed.

        :param station_id:          station ID
        :type station_id:           string
        :param time:                timepoint(s). Multiple times can be deleted at once.
        :type time:                 list of datatime.datetime
        :return:                    number of deleted datasets
        :rtype:                     integer
        """
        if not isinstance(time, list):
            time = [time]

        num_deleted_rows = 0
        with self._sql:
            for curr_time in time:
                # all cascaded datasets are also automatically deleted
                num_deleted_rows += self._sql.execute(" \
                    DELETE \
                    FROM WeatherData \
                    WHERE stationID=(?) AND time=(?)",
                                                      (station_id, curr_time)).rowcount

        return num_deleted_rows

    def get_data(self, station_id, first_time, last_time):
        """
        Obtains the base station data for the specified time interval from the table in the database.

        :param station_id:          station ID
        :type station_id:           string
        :param first_time:          beginning of the interval (inclusive)
        :type first_time:           datetime.datetime
        :param last_time:           end of the interval (inclusive)
        :type last_time:            datetime.datetime
        :return:                    timepoints, base station data
        :rtype:                     list of datetime.datetime, list of common.datastructures.BaseStationSensorData
        """
        base_data_from_db = self._sql.execute(" \
            SELECT time, pressure, UV \
            FROM WeatherData \
            WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
            ORDER BY time",
                                              (station_id, first_time, last_time)).fetchall()
        times = []
        base_data = []
        for base_data_for_timepoint in base_data_from_db:  # type: dict
            times.append(base_data_for_timepoint["time"])
            base_data.append(BaseStationSensorData(base_data_for_timepoint["pressure"], base_data_for_timepoint["UV"]))

        return times, base_data


class _CombiSensorDefinitionTable(object):
    """
    Representing the table 'CombiSensor' within a SQL weather database.
    Note: Any class method call must be embedded within a SQL-database lock (in a with-statement)
    """
    def __init__(self, sql):
        """
        Constructor.

        :param sql:                     parent SQL database connection object
        :type sql:                      sqlite3.Connection
        """
        self._sql = sql
        self._sql.row_factory = sqlite3.Row

        self._sql.execute(" \
            CREATE TABLE IF NOT EXISTS CombiSensor \
            ( \
                sensorID VARCHAR(10) NOT NULL PRIMARY KEY, \
                description VARCHAR(255) \
            )")

    def add(self, sensor_id, description):
        """
        Adds a combi sensor (temperature + humidity) to the table in the database.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :param description:             description of the sensor (location, type, specialities, ...)
        :type description:              string
        :raise AlreadyExistingError:    if the sensor ID already exists in the database
        """
        if self.exists(sensor_id):
            raise AlreadyExistingError("The sensor ID already exists in the database")
        else:
            self._sql.execute(" \
                INSERT INTO CombiSensor ( \
                    sensorID, \
                    description \
                ) VALUES (?,?)",
                              (sensor_id, description))

    def replace(self, sensor_id, description):
        """
        Replaces an existing combi sensor description without changing the other data.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :param description:             description of the sensor (location, type, specialities, ...)
        :type description:              string
        :raise NotExistingError:        if the combi sensor ID does not exist in the database
        """
        with self._sql:
            num_updated_rows = self._sql.execute(" \
                    UPDATE CombiSensor \
                    SET description=(?) \
                    WHERE sensorID=(?)",
                                                 (description, sensor_id)).rowcount

            if num_updated_rows == 0:
                raise NotExistingError("The combi sensor ID is not existing")

    def exists(self, sensor_id):
        """
        Checks if a combi sensor exists in the database.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :return:                        True if the combi sensor exists in the database, false otherwise
        :rtype:                         boolean
        """
        with self._sql:
            is_existing = self._sql.execute(" \
                   SELECT EXISTS ( \
                       SELECT * \
                       FROM CombiSensor \
                       WHERE sensorID=(?) \
                   )", (sensor_id,)).fetchone()[0]

        return is_existing

    def get_combi_sensor_ids(self):
        """
        Obtains all combi sensors registered in the database.

        :return:                        list of the IDs of all combi sensors registered in the database
        :rtype:                         list of string
        """
        combi_sensor_rows = self._sql.execute(" \
            SELECT sensorID \
            FROM CombiSensor \
            ORDER BY sensorID").fetchall()  # type: list of dict

        combi_sensor_ids = [item["sensorID"] for item in combi_sensor_rows]
        return combi_sensor_ids

    def remove(self, sensor_id):
        """
        Removes an existing combi sensor from the database.

        :param sensor_id:               combi sensor ID
        :type sensor_id:                string
        :return:                        True if the sensor has been deleted, False otherwise
        :rtype:                         boolean
        """
        is_deleted = self._sql.execute(" \
            DELETE \
            FROM CombiSensor \
            WHERE sensorID=(?)",
                                       (sensor_id,)).rowcount

        return is_deleted

    def get_sensor_descriptions(self):
        """
        Obtains the descriptions all combi sensors in the database.

        :return:                        descriptions of all combi sensors in the database
        :rtype:                         dict(string,string)
        """
        combi_sensors = self._sql.execute(" \
            SELECT sensorID, description \
            FROM CombiSensor").fetchall()

        sensor_descriptions = dict()
        for combi_sensor in combi_sensors:  # type: dict
            sensor_descriptions[combi_sensor["sensorID"]] = combi_sensor["description"]

        return sensor_descriptions
