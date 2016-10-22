import unittest
from weathernetwork.server.config import FTPWeatherServerConfigFile

class TestServerConfig(unittest.TestCase):
    def setUp(self):
        self._file_name = "./data/config_ftp_weather_server.ini"
        self._file_name_2 = "./data/config_ftp_weather_server_2.ini"

    def tearDown(self):
        pass

    def test_read(self):
        configFile = FTPWeatherServerConfigFile(self._file_name)
        configuration = configFile.read()

    def test_write(self):
        configFile = FTPWeatherServerConfigFile(self._file_name)
        configuration = configFile.read()

        configFile_2 = FTPWeatherServerConfigFile(self._file_name_2)
        configFile_2.write(configuration)


if __name__ == '__main__':
    unittest.main()
