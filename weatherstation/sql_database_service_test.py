import unittest
from weathernetwork.server.weathermessage import WeatherMessage
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory, SQLDatabaseService, SQLWeatherDB
import datetime
from weathernetwork.server.exceptions import NotExistingError, AlreadyExistingError
from weathernetwork.common.stationmetadata import WeatherStationMetadata
from weathernetwork.common.combisensorarray import CombiSensorArray
from weathernetwork.common.airsensordataset import AirSensorDataset
from weathernetwork.common.sensor import BaseStationSensorData, WindSensorData, CombiSensorData
from weathernetwork.common.weatherstationdataset import WeatherStationDataset

class SQLDatabaseService_test(unittest.TestCase):
    def setUp(self):
        """Sets up each unit test."""
        self._db_file_name = "data/weather.db"
        self._message_ID = "54321"
        self._station_ID = "TES2"
        self._not_existing_station_ID = "TES5"
        self._sensor_IDs = ["OUT1"]
        sensor_array = CombiSensorArray()
        sensor_array.add_sensor("OUT1", AirSensorDataset(30.9, 89.3))
        #self._data = WeatherDataset( datetime.datetime.utcnow(), sensor_array, 532.3, 1024.3, 9.8, 341.4, 34.2, 10.9, 21.9)


    def tearDown(self):
        """Finishes each unit test."""


    def test_add_station(self):
        db_file_name = "data/weather.db";

        weather_station = WeatherStationMetadata("TES", "TE923 Mebus", "Test City", "49.234", "11.024", "440")
        weather_station_2 = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City", "49.234", "11.024", "450")
        weather_station_2_B = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City 2", "49.234", "11.024", "450")

        weather_db = SQLWeatherDB(db_file_name)
        if not weather_db.combi_sensor_exists("OUT1"):
            weather_db.add_combi_sensor("OUT1", "outside sensor 1")
        sensor_IDs = weather_db.get_all_sensor_IDs()
        test_description = weather_db.get_sensor_description( ["OUT1", "temperature"] )
        if not weather_db.station_exists( weather_station.get_station_ID() ):
            weather_db.add_station(weather_station)
        if not weather_db.station_exists( weather_station_2.get_station_ID() ):
            weather_db.add_station(weather_station_2)

        weather_db.replace_station(weather_station_2_B);

        curr_time = datetime.datetime.utcnow()
        data = WeatherStationDataset()
        data.add_sensor(BaseStationSensorData(1032.4, 12.4, 8.5))
        data.add_sensor(WindSensorData(12.4, 43.9, 180.0, 15.2))
        data.add_sensor(CombiSensorData("OUT1", 34.9, 89.7))

        value = data.get_sensor_value( ["OUT1", "temperature"])


        combi_sensor_data = CombiSensorArray( AirSensorDataset( 20.5, 61.3 ), AirSensorDataset( 30.9, 80.5 ), AirSensorDataset( None, None ), AirSensorDataset( None, None ), AirSensorDataset( None, None ), AirSensorDataset( None, None ) )

        dataset_1 = WeatherDataset(curr_time, combi_sensor_data.get_vals(), 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_2 = WeatherDataset(curr_time + datetime.timedelta(5), combi_sensor_data.get_vals(), 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_3 = WeatherDataset(curr_time + datetime.timedelta(10), combi_sensor_data.get_vals(), 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_4 = WeatherDataset(curr_time + datetime.timedelta(15), combi_sensor_data.get_vals(), 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)

        weather_db.add_dataset("TES", dataset_1)
        weather_db.add_dataset("TES2", [dataset_2, dataset_3, dataset_4])

        weather_db.replace_dataset("TES2", dataset_2)

        removed_items = weather_db.remove_dataset("TES2", [dataset_2.get_time(), dataset_3.get_time()])

        weather_db.remove_station("TES")

        first_time = datetime.datetime(2016, 8, 20)
        last_time = datetime.datetime(2016, 9, 27)
        data = weather_db.get_data_in_time_range("TES2", first_time, last_time)


    def test_not_exsting_station(self):
        with self.assertRaises(NotExistingError):
            sql_database_service = SQLDatabaseService(self._db_file_name)
            message = WeatherMessage(self._message_ID, self._not_existing_station_ID, self._data)
            sql_database_service.add_data(message)


    def test_store_twice(self):
        sql_database_service = SQLDatabaseService(self._db_file_name)
        message = WeatherMessage(self._message_ID, self._station_ID, self._data)
        sql_database_service.add_data(message)
        with self.assertRaises(AlreadyExistingError):
            sql_database_service.add_data(message)


if __name__ == '__main__':
    unittest.main()
