import sqlite3
import datetime
from weathernetwork.common.combisensorarray import CombiSensorArray
from weathernetwork.server.exceptions import AlreadyExistingError
from weathernetwork.server.exceptions import NotExistingError
from weathernetwork.server.interface import IDatabaseService, IDatabaseServiceFactory
from weathernetwork.common.weatherstationdataset import WeatherStationDataset


class SQLDatabaseService(IDatabaseService):
    """SQL weather database service"""
    def __init__(self, db_file_name):
        self._observers = []
        self._database = SQLWeatherDB(db_file_name, CombiSensorArray.get_sensors())


    def add_data(self, message):
        """
        Stores the dataset in the database.
        """
        data = message.get_data()
        station_ID = message.get_station_ID()
        message_ID = message.get_message_ID()

        # concurrent calls to the database are allowed
        self._database.add_dataset(station_ID, data)

        # trigger acknowledgment to the client
        self._notify_observers(message_ID)


    def register_observer(self, observer):
        """Registers a new observer.
        """
        self._observers.append(observer)


    def unregister_observer(self, observer):
        self._observers.remove(observer)


    def _notify_observers(self, finished_ID):
        for observer in self._observers:
            observer.acknowledge_persistence(finished_ID)
        

class SQLDatabaseServiceFactory(IDatabaseServiceFactory):
    """Factory for weather database services"""
    def __init__(self, db_file_name):
        self._db_file_name = db_file_name


    def create(self):
        return SQLDatabaseService(self._db_file_name)


class SQLWeatherDB(object):
    """
    Persistent weather SQL-database.
    SQLlite can handle concurrency, i.e. multiple concurrent class of the class are allowed at any time.
    """
    def __init__(self, db_file):
        """
        Constructor.
        :param db_file:             name and path of the SQLite-database file
        :type db_file:              string
        """
        # open the database
        self._sensor_descriptions = WeatherStationDataset.get_sensor_descriptions()
        self._sql = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self._sql.row_factory = sqlite3.Row
       
        with self._sql:
            self._sql.execute( " \
                CREATE TABLE IF NOT EXISTS WeatherStation \
                ( \
                    stationID VARCHAR(10) NOT NULL PRIMARY KEY, \
                    device VARCHAR(255) NOT NULL, \
                    location VARCHAR(255) NOT NULL, \
                    latitude REAL NOT NULL, \
                    longitude REAL NOT NULL, \
                    height REAL NOT NULL \
                )" )
            self._sql.execute( " \
                CREATE TABLE IF NOT EXISTS WeatherData \
                ( \
                    stationID VARCHAR(10) NOT NULL, \
                    time TIMESTAMP NOT NULL, \
                    rainGauge REAL, \
                    pressure REAL, \
                    UV REAL, \
                    FOREIGN KEY(stationID) \
                        REFERENCES WeatherStation(stationID) \
                        ON DELETE CASCADE \
                        ON UPDATE CASCADE, \
                    PRIMARY KEY(stationID, time) \
                )" )

            self._sql.execute( " \
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

            self._sql.execute( " \
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

            self._sql.execute( " \
                CREATE TABLE IF NOT EXISTS CombiSensor \
                ( \
                    sensorID VARCHAR(10) NOT NULL PRIMARY KEY, \
                    description VARCHAR(255) \
                )")
                  
            self._sql.execute("PRAGMA foreign_keys = ON")
                        

    def close_database(self):
        """
        Dispose method used for guaranteed closing of the database connection.
        """
        self._sql.close()


    def _add_to_WeatherStation_table(self, sql, time, station_ID, rain_gauge, pressure, UV):
        """
        Adds a new dataset to the WeatherStation SQL-table.
        :param sql:                 SQL-object of the database. This method needs to be encapsulated by a transaction.
        """
        try:
            self._sql.execute( " \
                INSERT INTO WeatherData ( \
                    time, \
                    stationID, \
                    rainGauge, \
                    pressure, \
                    UV \
                ) VALUES (?,(SELECT stationID from WeatherStation WHERE stationID=(?)),?,?,?)", \
                ( self._round_time(time), station_ID, rain_gauge, pressure, UV ) )
        except sqlite3.Error as e:
            if "NULL" in e.args[0]:
                raise NotExistingError("The station does not exist in the database")
            elif "unique" in e.args[0]:
                raise AlreadyExistingError("For the given station (%s), a dataset for the given time (%s) already exists in the database" % (station_ID, str(time)))
            else:
                raise


    def _add_to_WindSensorData_table(self, sql, time, station_ID, wind_direction, wind_speed, wind_gust, wind_temp):
        """
        Adds a new dataset to the WindSensor SQL-table.
        :param sql:                 SQL-object of the database. This method needs to be encapsulated by a transaction.
        """
        self._sql.execute(" \
            INSERT INTO WindSensorData ( \
                time, \
                stationID, \
                direction, \
                speed, \
                gusts, \
                temperature \
            ) VALUES (?,?,?,?,?,?)", \
            ( self._round_time(time), station_ID, wind_direction, wind_speed, wind_gust, wind_temp ) )   


    def _add_to_CombiSensorData_table(self, sql, time, station_ID, combi_sensor_vals):
        """
        Adds a new dataset to the CombiSensorData SQL-table.
        :param sql:                 SQL-object of the database. This method needs to be encapsulated by a transaction.
        :param combi_sensor_vals:   list of CombiSensorDataset objects
        """
        for next_sensor_val in combi_sensor_vals:
            temperature = next_sensor_val.get_temperature()
            humidity = next_sensor_val.get_humidity()
            sensor_ID = next_sensor_val.get_sensor_ID()
            try:
                self._sql.execute(" \
                    INSERT INTO CombiSensorData ( \
                        time, \
                        stationID, \
                        sensorID, \
                        temperature, \
                        humidity \
                    ) VALUES (?,?,(SELECT sensorID from CombiSensor WHERE sensorID=(?)),?,?)", \
                    ( self._round_time(time), station_ID, sensor_ID, temperature, humidity ) )     
            except sqlite3.Error as e:
                if "NULL" in e.args[0]:
                    raise NotExistingError("The combi sensor ID not exist in the database")
                elif "unique" in e.args[0]:
                    raise AlreadyExistingError("For the given combi sensor ID (%s), station ID (%s) and time (%s) already data exists in the database" % (sensor_ID, station_ID, str(time)))
                else:
                    raise 


    def add_dataset(self, station_ID, data):
        """
        Adds a new dataset to the database.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.
        If already data exists for the requested station, nothing is changed.
        :param station_ID:              station ID
        :type station_ID:               string
        :param data:                    data for (possibly several) timepoints
        :type data:                     single WeatherDataset object or list of multiple WeatherDataset objects
        :raise NotExistingError:        if a requested station or sensor ID is not existing in the database
        :raise AlreadyExistingError:    if a dataset is already existing in the database for the given station and time (and sensor ID)
        """
        if not isinstance(data,list):
            data = [data]

        with self._sql:
            # add the dataset to the database
            for dataset in data:
                # write the general information
                time = dataset.get_time()
                rain_gauge = dataset.get_rain_gauge()
                pressure = dataset.get_pressure()
                UV = dataset.get_UV()
                self._add_to_WeatherStation_table(self._sql, time, station_ID, rain_gauge, pressure, UV)

                # write the wind sensor information (here it is already guaranteed that a dataset for the given station and time existing in the database)
                wind_direction, wind_speed, wind_gust, wind_temp = dataset.get_wind()
                self._add_to_WindSensorData_table(self._sql, time, station_ID, wind_direction, wind_speed, wind_gust, wind_temp)
                    
                # write the temperature / humidity combi sensor information (again existence of station and time is guaranteed)
                combi_sensor_vals = dataset.get_combi_sensor_vals()
                self._add_to_CombiSensorData_table(self._sql, time, station_ID, combi_sensor_vals);
                                       

    def replace_dataset(self, station_ID, data):
        """
        Replaces an existing dataset.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.
        :param station_ID:          station ID
        :type station_ID:           string
        :param data:                data for (possibly several) timepoints
        :type data:                 single WeatherDataset object or list of multiple WeatherDataset objects
        :raise NotExistingError:    if no entry exists for the requested station and timepoint or sensor ID
        """
        if not isinstance(data,list):
            data = [data]

        with self._sql:
            for dataset in data:
                # write the general information
                time = dataset.get_time();
                rainGauge = dataset.get_rain_gauge();
                pressure = dataset.get_pressure();
                UV = dataset.get_UV();

                num_updated_rows = self._sql.execute( " \
                    UPDATE WeatherData \
                    SET rainGauge=(?), pressure=(?), UV=(?) \
                    WHERE time=(?) AND stationID=(?)", \
                    ( rainGauge, pressure, UV, self._round_time(time), station_ID ) ).rowcount           
           
                if num_updated_rows == 0:
                    raise NotExistingError("No entry exists for the requested station at the requested time")

                # write the wind sensor information (here it is already guaranteed that a dataset for the given station and time existing in the database)
                wind_direction, wind_speed, wind_gust, wind_temp = dataset.get_wind();

                self._sql.execute( " \
                    UPDATE WindSensorData \
                    SET direction=(?), speed=(?), gusts=(?), temperature=(?) \
                    WHERE time=(?) AND stationID=(?)", \
                    ( wind_direction, wind_speed, wind_gust, wind_temp, self._round_time(time), station_ID ) )           

                # write the temperature / humidity combi sensor information (again existence of station and time is guaranteed)
                combi_sensor_vals = dataset.get_combi_sensor_vals()
                for next_sensor_val in combi_sensor_vals:
                    temperature = next_sensor_val.get_temperature()
                    humidity = next_sensor_val.get_humidity()
                    sensor_ID = next_sensor_val.get_sensor_ID()
                    num_updated_rows = self._sql.execute( " \
                        UPDATE CombiSensorData \
                        SET temperature=(?), humidity=(?) \
                        WHERE time=(?) AND stationID=(?) AND sensorID=(?)", \
                        ( temperature, humidity, self._round_time(time), station_ID, sensor_ID ) )

                    if num_updated_rows == 0:
                        raise NotExistingError("The requested combi sensor ID does not exist")


    def _round_time(self, time):
        """
        Rounds the given time to seconds
        :param time:            timepoint
        :type time:             datetime
        """
        return time.replace(microsecond=0)


    def remove_dataset(self, station_ID, time):
        """
        Deletes the given dataset. UNDO is NOT possible.
        :param station_ID:          station ID
        :type station_ID:           string
        :param time:                timepoint(s). Multiple times can be deleted at once.
        :type time:                 datetime or list of datatime objects
        :return:                    number of deleted datasets
        :rtype:                     integer
        """
        if not isinstance(time, list):
            time = [time]

        num_deleted_rows = 0
        with self._sql:
            for curr_time in time:
                # all cascaded datasets are also automatically deleted
                num_deleted_rows += self._sql.execute( " \
                    DELETE \
                    FROM WeatherData \
                    WHERE stationID=(?) AND time=(?)", \
                    ( station_ID, self._round_time(curr_time) ) ).rowcount

        return num_deleted_rows


    def get_data_in_time_range(self, station_ID, first_time, last_time):
        """
        Returns all datasets for the given station within the given time range.
        :param station_ID:          station ID
        :type station_ID:           string
        :param first_time:          begining of the requested time range (inclusive)
        :type first_time:           datetime
        :param last_time:           end of the requested time range (inclusive)
        :type last_time:            datetime
        :return:                    weather datasets for the requested timepoints, sorted by ascending time. If no data exists for the requested range, it is empty.
        :rtype:                     list of WeatherDataset objects
        """
        with self._sql:
            base_data_from_db = self._sql.execute( " \
                SELECT * \
                FROM WeatherData \
                WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
                ORDER BY time", \
                ( station_ID, first_time, last_time ) ).fetchall()
            base_data_in_range = [ dict( item ) for item in base_data_from_db ]

            wind_data_from_db = self._sql.execute( " \
                SELECT * \
                FROM WindSensorData \
                WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
                ORDER BY time", \
                ( station_ID, first_time, last_time ) ).fetchall()
            wind_data_in_range = [ dict( item ) for item in wind_data_from_db ]

            # iterate over all times in the time range in order
            datasets = []
            for base, wind in zip( base_data_in_range, wind_data_in_range ):
                time = base["time"]

                combi_data_from_db = self._sql.execute( " \
                        SELECT temperature, humidity, sensorID \
                        FROM CombiSensorData \
                        WHERE stationID=(?) AND time=(?) \
                        ORDER BY sensorID", \
                        ( station_ID, time ) ).fetchall()

                combi_data = []
                for sensor_data in combi_data_from_db:
                    sensor_ID = sensor_data["sensorID"]
                    combi_data.append( CombiSensorDataset(sensor_ID, sensor_data["temperature"], sensor_data["humidity"]) )
                    
                datasets.append( WeatherDataset( base["time"], combi_data, base["rainGauge"], base["pressure"], base["UV"], wind["direction"], wind["speed"], wind["gusts"], wind["temperature"] ) )

        return datasets


    def add_station(self, station):
        """
        Adds a new weather station to the database.
        :param station:                 metadata of the station
        :type station:                  WeatherStationMetaData object
        :raise AlreadyExistingError:    if the station is already existing in the database
        """
        identifier = station.get_station_ID();
        device = station.get_device_info();
        location = station.get_location_info();
        latitude, longitude, height = station.get_geo_info();

        with self._sql:
            try:
                self._sql.execute( " \
                    INSERT INTO WeatherStation ( \
                        stationID, \
                        device, \
                        location, \
                        latitude, \
                        longitude, \
                        height) VALUES (?,?,?,?,?,?)", \
                        ( identifier, device, location, latitude, longitude, height ) )                  
            except sqlite3.Error as e:
                raise AlreadyExistingError("The station is already existing")


    def replace_station(self, station):
        """
        Replaces the metadata of an existing weather station in the database. DO NOT USE this method if a station has been relocated to a new place. Create instead a new station with a new identifier.
        :param station:                 metadata of the station
        :type station:                  WeatherStationMetaData object
        :raise NotExistingError:        if the station is not existing in the database
        """
        identifier = station.get_station_ID();
        device = station.get_device_info();
        location = station.get_location_info();
        latitude, longitude, height = station.get_geo_info();

        with self._sql:
            num_updated_rows = self._sql.execute( " \
                UPDATE WeatherStation \
                SET device=(?), location=(?), latitude=(?), longitude=(?), height=(?) \
                WHERE stationID=(?) ", \
                ( device, location, latitude, longitude, height, identifier ) ).rowcount           
           
            if num_updated_rows == 0:
                raise NotExistingError("The station is not existing")


    def remove_station(self, station_ID):
        """
        Removes an existing station from the database. All weather data entries are also deleted.
        :param station_ID:              station ID
        :type station_ID:               string
        :return:                        success flag of the remove operation (true: removal was successfull, false: otherwise)
        :rtype:                         boolean
        """
        with self._sql:
            num_deleted_rows = self._sql.execute( " \
                DELETE \
                FROM WeatherStation \
                WHERE stationID=(?)", \
                ( station_ID, ) ).rowcount

        if num_deleted_rows == 1:
            return True
        else:
            return False


    def station_exists(self, station_ID):
        """
        Checks if a station exists in the database.
        :param station_ID:              station ID
        :type station_ID:               string
        :return:                        True if the station exists in the database, false otherwise
        :rtype:                         boolean
        """
        with self._sql:
            is_existing = self._sql.execute( " \
                SELECT EXISTS ( \
                    SELECT * \
                    FROM WeatherStation \
                    WHERE stationID=(?) \
                )", ( station_ID, ) ).fetchone()[0]

        return is_existing


    def add_combi_sensor(self, sensor_ID, description):
        """
        Adds a combi sensor (temperature + humidity). If it already exists in the database, nothing is changed.
        :param sensor_ID:               combi sensor ID
        :type sensor_ID:                string
        :param description:             description of the sensor (location, type, specialities, ...)
        :type descrption:               string
        :raise AlreadyExistingError:    if the sensor ID already exists in the database
        """
        if sensor_ID in self.get_all_sensor_IDs():
            raise AlreadyExistingError("The sensor ID already exists in the database")

        with self._sql:
            self._sql.execute( " \
                INSERT OR IGNORE INTO CombiSensor ( \
                    sensorID, \
                    description \
                ) VALUES (?,?)", \
                ( sensor_ID, description ) )


    def replace_combi_sensor(self, sensor_ID, description):
        """
        Replaces an existing combi sensor description without changing the data.
        :param sensor_ID:               combi sensor ID
        :type sensor_ID:                string
        :param description:             description of the sensor (location, type, specialities, ...)
        :type descrption:               string
        :raise NotExistingError:        if the combi sensor ID does not exist in the database
        """
        with self._sql:
            num_updated_rows = self._sql.execute( " \
                UPDATE CombiSensor \
                SET description=(?) \
                WHERE sensorID=(?)", \
                ( description, sensor_ID ) ).rowcount           
           
            if num_updated_rows == 0:
                raise NotExistingError("The combi sensor ID is not existing")


    def combi_sensor_exists(self, sensor_ID):
        """
        Checks if a combi sensor exists in the database.
        :param sensor_ID:               combi sensor ID
        :type sensor_ID:                string
        :return:                        True if the combi sensor exists in the database, false otherwise
        :rtype:                         boolean
        """
        with self._sql:
            is_existing = self._sql.execute( " \
                SELECT EXISTS ( \
                    SELECT * \
                    FROM CombiSensor \
                    WHERE sensorID=(?) \
                )", ( sensor_ID, ) ).fetchone()[0]

        return is_existing


    def _get_combi_sensor_IDs(self):
        """
        Obtains all combi sensors registered in the database.
        """
        with self._sql:
            combi_sensor_rows = self._sql.execute( " \
                SELECT sensorID \
                FROM CombiSensor \
                ORDER BY sensorID" ).fetchall()

        combi_sensor_IDs = [item["sensorID"] for item in combi_sensor_rows]
        return combi_sensor_IDs


    def _get_combi_sensor_description(self, sensor_ID):
        """
        Obtains the description of a combi sensor.
        """
        with self._sql:
            combi_sensor_row = self._sql.execute( " \
                SELECT description \
                FROM CombiSensor \
                WHERE sensorID=(?)", \
                ( sensor_ID, ) ).fetchone()

        if not combi_sensor_row:
            raise NotExistingError("The sensor ID is not existing")

        return combi_sensor_row[0]


    def remove_combi_sensor(self, sensor_ID):
        """
        Removes an existing combi sensor from the database.
        :param sensor_ID:               combi sensor ID
        :type sensor_ID:                string

        """
        with self._sql:
            is_deleted = self._sql.execute( " \
                DELETE \
                FROM CombiSensor \
                WHERE sensorID=(?)", \
                ( sensor_ID, ) ).rowcount

        return is_deleted


    def get_sensor_description(self, sensor_ID_list):
        """
        Obtains the description of a certain sensor ID.
        """
        if not isinstance(sensor_ID_list, list):
            sensor_ID_list = [sensor_ID_list]
        sensor_ID = sensor_ID_list[0]
        if len(sensor_ID_list) > 1:
            subsensor_ID = sensor_ID_list[1]
        else:
            subsensor_ID = None

        if sensor_ID in self._sensor_descriptions:
            if not subsensor_ID:
                description = self._sensor_descriptions[sensor_ID]
            else:
                description = self._sensor_descriptions[sensor_ID][subsensor_ID]
        else:
            description = self._get_combi_sensor_description(sensor_ID)
            description += " (" + self._sensor_descriptions["combiSensor"][subsensor_ID] + ")"
        
        if isinstance(description, dict):
            raise NotExistingError("This sensor has several subsensors, none is specified.")
            
        return description


    def get_all_sensor_IDs(self):
        """
        Obtains the IDs of all sensors stored in the database.
        """
        sensor_ID_dict = dict()

        # regular sensors
        sensor_IDs = list(self._sensor_descriptions.keys())
        for sensor_ID in sensor_IDs:
            if isinstance(self._sensor_descriptions[sensor_ID], dict):
                sensor_ID_dict[sensor_ID] = list(self._sensor_descriptions[sensor_ID].keys())
            else:
                sensor_ID_dict[sensor_ID] = None

        del sensor_ID_dict["combiSensor"]

        # combi sensors
        sensor_IDs = self._get_combi_sensor_IDs()
        for sensor_ID in sensor_IDs:
            sensor_ID_dict[sensor_ID] = list(self._sensor_descriptions["combiSensor"].keys())

        return sensor_ID_dict
