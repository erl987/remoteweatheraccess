import threading
import sqlite3
import datetime

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
                                    identifier TEXT PRIMARY KEY, \
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
                                    temperature FLOAT, \
                                    humidity FLOAT, \
                                    rainGauge FLOAT, \
                                    pressure FLOAT, \
                                    UV FLOAT, \
                                    windDirection FLOAT, \
                                    windSpeed FLOAT, \
                                    windGust FLOAT, \
                                    windTemp FLOAT, \
                                    FOREIGN KEY(stationID) REFERENCES WeatherStations(identifier) ON DELETE CASCADE, \
                                    PRIMARY KEY(stationID, time) \
                                    )" )

            self._sql.execute("PRAGMA foreign_keys = ON")


    def close_database(self):
        """
        Dispose method used for guaranteed closing of the database connection.
        """
        self._sql.close()


    def add_dataset(self, station_identifier, dataset):
        """
        Adds a new dataset to the database.
        """
        self._insert_dataset(station_identifier, dataset, False)


    def replace_dataset(self,station_identifier, dataset):
        """
        Replaces an existing dataset. If this dataset does not exist, it will be inserted.
        """
        self._insert_dataset(station_identifier, dataset, True)


    def _insert_dataset(self, station_identifier, data, is_replace):
        """
        Inserts the dataset into the database (inserting or replacing as required)
        Note: The performance is limited to about 50 row/s. Add multiple rows at once for better performance.
        """
        if not isinstance(data,list):
            data = [data]

        with self._lock:
            with self._sql:
                if is_replace:
                    commandStr = "REPLACE"
                else:
                    commandStr = "INSERT"

                # add the dataset to the database
                for dataset in data:
                    # read the data for that dataset
                    time = dataset.get_time();
                    temperature = dataset.get_temperature();
                    humidity = dataset.get_humidity();
                    rainGauge = dataset.get_rain_gauge();
                    pressure = dataset.get_pressure();
                    UV = dataset.get_UV();
                    windDirection, windSpeed, windGust, windTemp = dataset.get_wind();

                    # write it to the database
                    try:
                        self._sql.execute( "%s INTO WeatherData ( \
                                                time, \
                                                stationID, \
                                                temperature, \
                                                humidity, \
                                                rainGauge, \
                                                pressure, \
                                                UV, \
                                                windDirection, \
                                                windSpeed, \
                                                windGust, \
                                                windTemp \
                                                ) VALUES (?,(SELECT identifier from WeatherStations WHERE identifier=(?)),?,?,?,?,?,?,?,?,?)" % commandStr, \
                                                    ( time.replace(microsecond=0), station_identifier, temperature, humidity, rainGauge, pressure, UV, windDirection, windSpeed, windGust, windTemp ) )
                    except sqlite3.Error as e:
                        if "NULL" in e.args[0]:
                            raise NameError("The station does not exist in the database")
                        elif "unique" in e.args[0]:
                            raise NameError("For the given station, a dataset for the given time already exists in the database")
                        else:
                            raise NameError(e)


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
                    num_deleted_rows += self._sql.execute( "DELETE \
                                                            FROM WeatherData \
                                                            WHERE stationID=(?) AND time=(?)", \
                                                                ( station_ID, curr_time.replace(microsecond=0) ) ).rowcount

        return num_deleted_rows


    def get_data_in_time_range(self, station_identifier, first_time, last_time):
        """
        Returns all datasets for the given station within the given time range (including the end of the time range)
        """
        with self._lock:
            with self._sql:
                data_from_db = self._sql.execute( " \
                                                    SELECT * \
                                                    FROM WeatherData \
                                                    WHERE stationID=(?) AND time BETWEEN (?) AND (?)", \
                                                        ( station_identifier, first_time, last_time ) ).fetchall()

        data_in_range = [ dict( item ) for item in data_from_db ]

        return data_in_range


    def add_station(self, station):
        """
        Adds a new weather station to the database
        """
        self._insert_station(station, False)


    def replace_station(self,station):
        """
        Replaces the metadata of an existing weather station in the database. DO NOT USE this method if a station has been relocated to a new place. Create instead a new station with a new identifier.
        """
        self._insert_station(station, True)


    def _insert_station(self, station, is_replace):
        """
        Inserts weather station metadata to the database
        """
        identifier = station.get_identifier();
        device = station.get_device_info();
        location = station.get_location_info();
        latitude, longitude, height = station.get_geo_info();

        with self._lock:
            with self._sql:
                if is_replace:
                    commandStr = "REPLACE"
                else:
                    commandStr = "INSERT"

                # inserting fails silently if the station already exists
                try:
                    self._sql.execute( "%s INTO WeatherStations ( \
                                        identifier, \
                                        device, \
                                        location, \
                                        latitude, \
                                        longitude, \
                                        height) VALUES (?,?,?,?,?,?)" % commandStr, \
                                            ( identifier, device, location, latitude, longitude, height ) )           
                except sqlite3.Error as e:
                    raise NameError("The station is already existing")


    def remove_station(self, station_ID):
        """
        Removes an existing station from the database. All weather data entries are also deleted.
        """
        with self._lock:
            with self._sql:
                num_deleted_rows = self._sql.execute( "DELETE \
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
                is_existing = self._sql.execute( "SELECT EXISTS (SELECT * FROM WeatherStations WHERE identifier=(?))", ( station_ID, ) ).fetchone()[0]

        return is_existing