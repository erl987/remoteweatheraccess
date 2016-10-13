import unittest
from weathernetwork.server.weathermessage import WeatherMessage
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory, SQLDatabaseService, SQLWeatherDB
import datetime
from weathernetwork.server.exceptions import NotExistingError, AlreadyExistingError
from weathernetwork.common.sensor import WeatherStationMetadata, RainSensorData
from weathernetwork.common.sensor import BaseStationSensorData, WindSensorData, CombiSensorData
from weathernetwork.common.weatherstationdataset import WeatherStationDataset
from datetime import timedelta

class SQLDatabaseService_test(unittest.TestCase):
    def setUp(self):
        """Sets up each unit test."""
        self._db_file_name = "data/weather.db"
        self._message_ID = "54321"
        self._station_ID = "TES2"
        self._not_existing_station_ID = "TES5"
        self._sensor_IDs = ["OUT1"]

        curr_time = datetime.datetime(year=2016, month=9, day=25, hour=18, minute=30, second=30)
        base_station_sensor_data = BaseStationSensorData(1032.4, 8.5)
        wind_sensor_data = WindSensorData(12.4, 43.9, 180.0, 15.2)
        combi_sensor_data = CombiSensorData("OUT1", 34.9, 89.7, "outside sensor 1")

        self._dataset_1 = WeatherStationDataset(curr_time)
        rain_sensor_data_1 = RainSensorData(12.5, curr_time - timedelta(minutes=10))
        self._dataset_1.add_sensor(base_station_sensor_data)
        self._dataset_1.add_sensor(rain_sensor_data_1)
        self._dataset_1.add_sensor(wind_sensor_data)
        self._dataset_1.add_sensor(combi_sensor_data)

        self._dataset_2 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=10))
        rain_sensor_data_2 = RainSensorData(10.5, self._dataset_2.get_time() - timedelta(minutes=10))
        self._dataset_2.add_sensor(base_station_sensor_data)
        self._dataset_2.add_sensor(rain_sensor_data_2)
        self._dataset_2.add_sensor(wind_sensor_data)
        self._dataset_2.add_sensor(combi_sensor_data)

        self._dataset_3 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=20))
        rain_sensor_data_3 = RainSensorData(9.2, self._dataset_3.get_time() - timedelta(minutes=10))
        self._dataset_3.add_sensor(base_station_sensor_data)
        self._dataset_3.add_sensor(rain_sensor_data_3)
        self._dataset_3.add_sensor(wind_sensor_data)
        self._dataset_3.add_sensor(combi_sensor_data)

        self._dataset_4 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=30))
        rain_sensor_data_4 = RainSensorData(15.5, self._dataset_4.get_time() - timedelta(minutes=10))
        self._dataset_4.add_sensor(base_station_sensor_data)
        self._dataset_4.add_sensor(rain_sensor_data_4)
        self._dataset_4.add_sensor(wind_sensor_data)
        self._dataset_4.add_sensor(combi_sensor_data)


    def tearDown(self):
        """Finishes each unit test."""


    def test_add_station(self):
        db_file_name = "data/weather.db";

        weather_station = WeatherStationMetadata("TES", "TE923 Mebus", "Test City", "49.234", "11.024", "440", 1.0)
        weather_station_2 = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City", "49.234", "11.024", "450", 1.0)
        weather_station_2_B = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City 2", "49.234", "11.024", "450", 1.0)

        weather_db = SQLWeatherDB(db_file_name)
        if not weather_db.combi_sensor_exists("OUT1"):
            weather_db.add_combi_sensor("OUT1", "outside sensor 1")
        sensor_IDs = self._dataset_1.get_all_sensor_IDs()
        test_description = self._dataset_1.get_sensor_description( ("OUT1", "temperature") )
        test_unit = self._dataset_1.get_sensor_unit( ("OUT1", "humidity") )

        if not weather_db.station_exists( weather_station.get_station_ID() ):
            weather_db.add_station(weather_station)
        if not weather_db.station_exists( weather_station_2.get_station_ID() ):
            weather_db.add_station(weather_station_2)

        weather_db.replace_station(weather_station_2_B);

        # testing obtaining single sensor values
        value = self._dataset_1.get_sensor_value( ("OUT1", "temperature") )

        # prepare the database
        weather_db.remove_dataset("TES", self._dataset_1.get_time())
        weather_db.remove_dataset("TES2", self._dataset_1.get_time())
        weather_db.remove_dataset("TES2", self._dataset_2.get_time())
        weather_db.remove_dataset("TES2", self._dataset_3.get_time())
        weather_db.remove_dataset("TES2", self._dataset_4.get_time())

        # testing adding datasets
        weather_db.add_dataset("TES", self._dataset_1)
        weather_db.add_dataset("TES2", [self._dataset_2, self._dataset_3, self._dataset_4])

        weather_db.replace_dataset("TES2", self._dataset_2)

        removed_items = weather_db.remove_dataset("TES2", [self._dataset_2.get_time(), self._dataset_3.get_time()])

        weather_db.remove_station("TES")

        first_time = datetime.datetime(2016, 8, 20)
        last_time = datetime.datetime(2016, 9, 27)
        dataset_1 = weather_db.get_data_in_time_range("TES2", first_time, last_time)


    def test_not_existing_station(self):
        with self.assertRaises(NotExistingError):
            sql_database_service = SQLDatabaseService(self._db_file_name)
            message = WeatherMessage(self._message_ID, self._not_existing_station_ID, self._dataset_1)
            sql_database_service.add_data(message)


    def test_store_twice(self):
        sql_database_service = SQLDatabaseService(self._db_file_name)
        message = WeatherMessage(self._message_ID, self._station_ID, self._dataset_1)
        sql_database_service.add_data(message)
        with self.assertRaises(AlreadyExistingError):
            sql_database_service.add_data(message)


if __name__ == '__main__':
    unittest.main()
