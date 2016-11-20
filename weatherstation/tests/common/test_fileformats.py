import unittest
import datetime
from weathernetwork.common.sensor import RainSensorData, BaseStationSensorData, WindSensorData, CombiSensorData, WeatherStationMetadata
from weathernetwork.common.weatherstationdataset import WeatherStationDataset
from datetime import timedelta
from weathernetwork.common.fileformats import PCWetterstationFormatFile
from weathernetwork.server.sqldatabase import SQLWeatherDB

class TestPCWetterstationFileProcessing(unittest.TestCase):
    def setUp(self):
        """Sets up each unit test."""
        self._file_path = "./data"

        # weather data
        curr_time = datetime.datetime(year=2016, month=9, day=30, hour=23, minute=40, second=30)
        base_station_sensor_data = BaseStationSensorData(1032.4, 8.5)
        wind_sensor_data = WindSensorData(12.4, 43.9, 180.0, 15.2)
        combi_sensor_data = CombiSensorData("OUT1", 34.9, 89.7, "outside sensor 1")

        dataset_1 = WeatherStationDataset(curr_time)
        rain_sensor_data_1 = RainSensorData(12.5, curr_time - timedelta(minutes=10))
        dataset_1.add_sensor(base_station_sensor_data)
        dataset_1.add_sensor(rain_sensor_data_1)
        dataset_1.add_sensor(wind_sensor_data)
        dataset_1.add_sensor(combi_sensor_data)

        dataset_2 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=10))
        rain_sensor_data_2 = RainSensorData(10.5, dataset_2.get_time() - timedelta(minutes=10))
        dataset_2.add_sensor(base_station_sensor_data)
        dataset_2.add_sensor(rain_sensor_data_2)
        dataset_2.add_sensor(wind_sensor_data)
        dataset_2.add_sensor(combi_sensor_data)

        dataset_3 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=20))
        rain_sensor_data_3 = RainSensorData(9.2, dataset_3.get_time() - timedelta(minutes=10))
        dataset_3.add_sensor(base_station_sensor_data)
        dataset_3.add_sensor(rain_sensor_data_3)
        dataset_3.add_sensor(wind_sensor_data)
        dataset_3.add_sensor(combi_sensor_data)

        dataset_4 = WeatherStationDataset(curr_time + datetime.timedelta(minutes=30))
        rain_sensor_data_4 = RainSensorData(15.5, dataset_4.get_time() - timedelta(minutes=10))
        dataset_4.add_sensor(base_station_sensor_data)
        dataset_4.add_sensor(rain_sensor_data_4)
        dataset_4.add_sensor(wind_sensor_data)
        dataset_4.add_sensor(combi_sensor_data)

        self._data_09_16 = [dataset_1, dataset_2]
        self._data = [dataset_1, dataset_2, dataset_3, dataset_4]

        # station data
        self._station_ID = "TES2"

        # database
        self._db_file_name = "./data/weather.db"
        self._first_time = datetime.datetime(2015,3, 1)
        self._last_time = datetime.datetime(2015, 3, 4)


    def tearDown(self):
        """Finishes each unit test."""


    def test_write_file(self):
        device_info = "Test weather station"
        location_info = "Test place"
        latitude = "50.5"
        longitude = "10.9"
        height = 203.5
        rain_calib_factor = 1.0
        station_metadata = WeatherStationMetadata(self._station_ID, device_info, location_info, latitude, longitude, height, rain_calib_factor)

        weather_data_file = PCWetterstationFormatFile( [ "OUT1" ] )
        weather_data_file.write(self._file_path, self._data, station_metadata)


    def test_write_from_database(self):
        weather_db = SQLWeatherDB(self._db_file_name)
        station_metadata = weather_db.get_station_metadata(self._station_ID)
        combi_sensor_ids = weather_db.get_combi_sensor_ids()
        data = weather_db.get_data_in_time_range(self._station_ID, self._first_time, self._last_time)
        weather_data_file = PCWetterstationFormatFile(combi_sensor_ids)
        weather_data_file.write(self._file_path, data, station_metadata)


    def test_read(self):
        file_name = "EXP03_15.csv"
        weather_data_file = PCWetterstationFormatFile( [ "OUT1" ] )
        datasets, rain_counter_base, station_metadata = weather_data_file.read(self._file_path + "/" + file_name, self._station_ID)


    def test_write_read_consistency(self):
        device_info = "Test weather station"
        location_info = "Test place"
        latitude = "50.5"
        longitude = "10.9"
        height = 203.5
        rain_calib_factor = 1.0
        station_metadata = WeatherStationMetadata(self._station_ID, device_info, location_info, latitude, longitude, height, rain_calib_factor)

        # write the weather data to file
        weather_data_file = PCWetterstationFormatFile( [ "OUT1" ] )
        weather_data_file.write(self._file_path, self._data_09_16, station_metadata)

        # read the weather data from file
        file_name = "EXP09_16.csv"
        weather_data_file = PCWetterstationFormatFile( [ "OUT1" ] )
        read_datasets, read_rain_counter_base, read_station_metadata = weather_data_file.read(self._file_path + "/" + file_name, self._station_ID)

        self.assertEqual(True, True)

if __name__ == '__main__':
    unittest.main()
