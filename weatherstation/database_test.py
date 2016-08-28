import unittest
import datetime
from weathernetwork.common.stationmetadata import WeatherStationMetadata
from weathernetwork.server.database import WeatherDB
from weathernetwork.common.weatherdataset import WeatherDataset

class Test_weather_db_test(unittest.TestCase):
    def test_add_station(self):
        db_file_name = "data/weather.db";

        weather_station = WeatherStationMetadata("TES", "TE923 Mebus", "Test City", "49.234", "11.024", "440")
        weather_station_2 = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City", "49.234", "11.024", "450")
        weather_station_2_B = WeatherStationMetadata("TES2", "TE923 Mebus", "Test City 2", "49.234", "11.024", "450")

        weather_db = WeatherDB(db_file_name)
        if not weather_db.station_exists( weather_station.get_identifier() ):
            weather_db.add_station(weather_station)
        if not weather_db.station_exists( weather_station_2.get_identifier() ):
            weather_db.add_station(weather_station_2)

        weather_db.replace_station(weather_station_2_B);

        curr_time = datetime.datetime.utcnow()
        dataset_1 = WeatherDataset(curr_time, 30.9, 80.5, 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_2 = WeatherDataset(curr_time + datetime.timedelta(5), 20.9, 80.5, 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_3 = WeatherDataset(curr_time + datetime.timedelta(10), 10.9, 80.5, 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)
        dataset_4 = WeatherDataset(curr_time + datetime.timedelta(15), 10.9, 80.5, 234.1, 1024.2, 8.9, 234, 23.1, 42.1, 29.0)

        weather_db.add_dataset("TES", dataset_1)
        weather_db.add_dataset("TES2", [dataset_2, dataset_3, dataset_4])

        weather_db.replace_dataset("TES2", dataset_2)

        removed_items = weather_db.remove_dataset("TES2", [dataset_2.get_time(), dataset_3.get_time()])

        weather_db.remove_station("TES")

        first_time = datetime.datetime(2016, 8, 20)
        last_time = datetime.datetime(2016, 9, 27)
        data = weather_db.get_data_in_time_range("TES2", first_time, last_time)


if __name__ == '__main__':
    unittest.main()
