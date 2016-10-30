import unittest
from weathernetwork.server.config import FTPWeatherServerIniFile, WeatherPlotServiceIniFile

class TestServerConfig(unittest.TestCase):
    def setUp(self):
        self._file_name = "./data/config_ftp_weather_server.ini"
        self._file_name_2 = "./data/config_ftp_weather_server_2.ini"

    def tearDown(self):
        pass

    def test_read(self):
        config_file = FTPWeatherServerIniFile(self._file_name)
        configuration = config_file.read()

    def test_write(self):
        config_file = FTPWeatherServerIniFile(self._file_name)
        configuration = config_file.read()

        config_file_2 = FTPWeatherServerIniFile(self._file_name_2)
        config_file_2.write(configuration)


class TestPlotterConfig(unittest.TestCase):
    def setUp(self):
        self._file_name = "./data/config_weather_plotter.ini"
        self._file_name_2 = "./data/config_weather_plotter_2.ini"

    def tearDown(self):
        pass

    def test_read(self):
        config_file = WeatherPlotServiceIniFile(self._file_name)
        configuration = config_file.read()

    def test_write(self):
        config_file = WeatherPlotServiceIniFile(self._file_name)
        configuration = config_file.read()

        config_file_2 = WeatherPlotServiceIniFile(self._file_name_2)
        config_file_2.write(configuration)


if __name__ == '__main__':
    unittest.main()
