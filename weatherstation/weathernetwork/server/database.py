import threading
import sqlite3
import datetime
from weathernetwork.common.weatherdataset import WeatherDataset

class WeatherDB(object):
    """
    Persistent weather SQL-database.
    This class is thread-safe.
    """
    def __init__(self, db_file):
        """
        Constructor.
        """
        # open the database
        self._lock = threading.Lock()
        self._sql = sqlite3.connect( db_file, check_same_thread=False ) # access by external connections may be corrupting data integrity
        self._sql.row_factory = sqlite3.Row
        with self._sql:
            self._sql.execute( "CREATE TABLE IF NOT EXISTS WeatherStations \
                                    ( \
                                    identifier TEXT NOT NULL PRIMARY KEY, \
                                    device TEXT NOT NULL, \
                                    location TEXT NOT NULL, \
                                    latitude FLOAT NOT NULL, \
                                    longitude FLOAT NOT NULL, \
                                    height FLOAT NOT NULL \
                                    )" )
            self._sql.execute( "CREATE TABLE IF NOT EXISTS WeatherData \
                                    ( \
                                    stationID INTEGER NOT NULL, \
                                    time DATETIME NOT NULL, \
                                    rainGauge FLOAT, \
                                    pressure FLOAT, \
                                    UV FLOAT, \
                                    FOREIGN KEY(stationID) \
                                        REFERENCES WeatherStations(identifier) \
                                        ON DELETE CASCADE \
                                        ON UPDATE CASCADE, \
                                    PRIMARY KEY(stationID, time) \
                                    )" )

            self._sql.execute( "CREATE TABLE IF NOT EXISTS WindSensor \
                                    ( \
                                    stationID INTEGER NOT NULL, \
                                    time DATETIME NOT NULL, \
                                    direction FLOAT, \
                                    speed FLOAT, \
                                    gusts FLOAT, \
                                    temperature FLOAT, \
                                    FOREIGN KEY(stationID, time) \
                                        REFERENCES WeatherData(stationID, time) \
                                        ON DELETE CASCADE \
                                        ON UPDATE CASCADE, \
                                    PRIMARY KEY(stationID, time) \
                                    )")

            self._sql.execute("PRAGMA foreign_keys = ON")


    def close_database(self):
        """
        Dispose method used for guaranteed closing of the database connection.
        """
        self._sql.close()


    def add_dataset(self, station_identifier, data):
        """
        Adds a new dataset to the database.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.
        """
        if not isinstance(data,list):
            data = [data]

        with self._lock:
            with self._sql:
                # add the dataset to the database
                for dataset in data:
                    time = dataset.get_time();
                    temperature = dataset.get_temperature();
                    humidity = dataset.get_humidity();
                    rainGauge = dataset.get_rain_gauge();
                    pressure = dataset.get_pressure();
                    UV = dataset.get_UV();

                    try:
                        self._sql.execute( " \
                            INSERT INTO WeatherData ( \
                                time, \
                                stationID, \
                                rainGauge, \
                                pressure, \
                                UV \
                            ) VALUES (?,(SELECT identifier from WeatherStations WHERE identifier=(?)),?,?,?)", \
                            ( self._round_time(time), station_identifier, rainGauge, pressure, UV ) )
                    except sqlite3.Error as e:
                        if "NULL" in e.args[0]:
                            raise NameError("The station does not exist in the database")
                        elif "unique" in e.args[0]:
                            raise NameError("For the given station, a dataset for the given time already exists in the database")
                        else:
                            raise NameError(e)

                    # write the wind sensor information (here it is already guaranteed that a dataset for the given station and time existing in the database)
                    wind_direction, wind_speed, wind_gust, wind_temp = dataset.get_wind();
                    self._sql.execute(" \
                        INSERT INTO WindSensor ( \
                            time, \
                            stationID, \
                            direction, \
                            speed, \
                            gusts, \
                            temperature \
                        ) VALUES (?,?,?,?,?,?)", \
                        ( self._round_time(time), station_identifier, wind_direction, wind_speed, wind_gust, wind_temp ) )       


    def replace_dataset(self, station_identifier, data):
        """
        Replaces an existing dataset.
        Note: The performance is limited to about 50 commits/s. Add multiple rows at once for better performance.
        """
        if not isinstance(data,list):
            data = [data]

        with self._lock:
            with self._sql:
                for dataset in data:
                    time = dataset.get_time();
                    temperature = dataset.get_temperature();
                    humidity = dataset.get_humidity();
                    rainGauge = dataset.get_rain_gauge();
                    pressure = dataset.get_pressure();
                    UV = dataset.get_UV();

                    num_updated_rows = self._sql.execute( " \
                        UPDATE WeatherData \
                        SET rainGauge=(?), pressure=(?), UV=(?) \
                        WHERE time=(?) AND stationID=(?)", \
                        ( rainGauge, pressure, UV, self._round_time(time), station_identifier ) ).rowcount           
           
                    if num_updated_rows == 0:
                        raise NameError("No entry exists for the requested station at the requested time")

                    # write the wind sensor information (here it is already guaranteed that a dataset for the given station and time existing in the database)
                    wind_direction, wind_speed, wind_gust, wind_temp = dataset.get_wind();

                    self._sql.execute( " \
                        UPDATE WindSensor \
                        SET direction=(?), speed=(?), gusts=(?), temperature=(?) \
                        WHERE time=(?) AND stationID=(?)", \
                        ( wind_direction, wind_speed, wind_gust, wind_temp, self._round_time(time), station_identifier ) )           


    def _round_time(self, time):
        """
        Rounds the given time to seconds
        """
        return time.replace(microsecond=0)


    def remove_dataset(self, station_ID, time):
        """
        Delete the given dataset. UNDO is NOT possible. Datasets for multiple times can be deleted at once.
        """
        if not isinstance(time, list):
            time = [time]

        num_deleted_rows = 0
        with self._lock:
            with self._sql:
                for curr_time in time:
                    # all cascaded datasets are also automatically deleted
                    num_deleted_rows += self._sql.execute( " \
                        DELETE \
                        FROM WeatherData \
                        WHERE stationID=(?) AND time=(?)", \
                        ( station_ID, self._round_time(curr_time) ) ).rowcount

        return num_deleted_rows


    def get_data_in_time_range(self, station_identifier, first_time, last_time):
        """
        Returns all datasets for the given station within the given time range (including the end of the time range)
        """
        with self._lock:
            with self._sql:
                base_data_from_db = self._sql.execute( " \
                    SELECT * \
                    FROM WeatherData \
                    WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
                    ORDER BY time", \
                    ( station_identifier, first_time, last_time ) ).fetchall()

                wind_data_from_db = self._sql.execute( " \
                    SELECT * \
                    FROM WindSensor \
                    WHERE stationID=(?) AND time BETWEEN (?) AND (?) \
                    ORDER BY time", \
                    ( station_identifier, first_time, last_time ) ).fetchall()
        
                base_data_in_range = [ dict( item ) for item in base_data_from_db ]
                wind_data_in_range = [ dict( item ) for item in wind_data_from_db ]

        datasets = []
        for base, wind in zip( base_data_in_range, wind_data_in_range ):
            datasets.append( WeatherDataset( base['time'], 0, 0, base["rainGauge"], base["pressure"], base["UV"], wind["direction"], wind["speed"], wind["gusts"], wind["temperature"] ) )

        return datasets


    def add_station(self, station):
        """
        Adds a new weather station to the database
        """
        identifier = station.get_identifier();
        device = station.get_device_info();
        location = station.get_location_info();
        latitude, longitude, height = station.get_geo_info();

        with self._lock:
            with self._sql:
                try:
                    self._sql.execute( " \
                        INSERT INTO WeatherStations ( \
                            identifier, \
                            device, \
                            location, \
                            latitude, \
                            longitude, \
                            height) VALUES (?,?,?,?,?,?)", \
                            ( identifier, device, location, latitude, longitude, height ) )                  
                except sqlite3.Error as e:
                    raise NameError("The station is already existing")


    def replace_station(self,station):
        """
        Replaces the metadata of an existing weather station in the database. DO NOT USE this method if a station has been relocated to a new place. Create instead a new station with a new identifier.
        """
        identifier = station.get_identifier();
        device = station.get_device_info();
        location = station.get_location_info();
        latitude, longitude, height = station.get_geo_info();

        with self._lock:
            with self._sql:
                num_updated_rows = self._sql.execute( " \
                    UPDATE WeatherStations \
                    SET device=(?), location=(?), latitude=(?), longitude=(?), height=(?) \
                    WHERE identifier=(?) ", \
                    ( device, location, latitude, longitude, height, identifier ) ).rowcount           
           
                if num_updated_rows == 0:
                    raise NameError("The station is not existing")


    def remove_station(self, station_ID):
        """
        Removes an existing station from the database. All weather data entries are also deleted.
        """
        with self._lock:
            with self._sql:
                num_deleted_rows = self._sql.execute( " \
                    DELETE \
                    FROM WeatherStations \
                    WHERE identifier=(?)", \
                    ( station_ID, ) ).rowcount

        if num_deleted_rows == 1:
            return True
        else:
            return False


    def station_exists(self, station_ID):
        """
        Checks if a station exists in the database
        """
        with self._lock:
            with self._sql:
                # all weather dataset entries are automatically deleted due to the configured cascade
                is_existing = self._sql.execute( " \
                    SELECT EXISTS ( \
                        SELECT * \
                        FROM WeatherStations \
                        WHERE identifier=(?) \
                    )", ( station_ID, ) ).fetchone()[0]

        return is_existing