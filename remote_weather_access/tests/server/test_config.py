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

import configparser
import os
import shutil
import unittest

from remote_weather_access.common.datastructures import BaseStationSensorData, RainSensorData
from remote_weather_access.server.config import DatabaseConfigSection, FTPReceiverConfigSection, PlotConfigSection, \
    LogConfigSection, FTPWeatherServerIniFile, FTPWeatherServerConfig, WeatherPlotServiceIniFile, \
    WeatherPlotServiceConfig, IniFileUtils


def db_file_name():
    return "database.db"


def ini_file_name():
    return file_directory() + os.sep + "weatherserver.ini"


def file_directory():
    return "./tests/workingDir/config"


def a_base_config():
    database_config = DatabaseConfigSection(db_file_name=db_file_name())
    log_config = LogConfigSection(log_file_name="log.txt",
                                  max_kbytes_per_file=100,
                                  num_files_to_keep=10)
    return database_config, log_config


def a_weather_server_config():
    ftp_receiver_config = FTPReceiverConfigSection(receiver_directory="./receiver_dir",
                                                   temp_data_directory="./temp_dir",
                                                   data_file_extension="ZIP",
                                                   time_between_data=10.0)
    database_config, log_config = a_base_config()
    return FTPWeatherServerConfig(database_config, ftp_receiver_config, log_config)


def a_plotter_service_config():
    plot_config = PlotConfigSection(
        sensors_to_plot=[(BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE),
                         (RainSensorData.RAIN, RainSensorData.CUMULATED)],
        graph_directory="./graph_dir",
        graph_file_name="graph.png",
        time_period_duration=7)
    database_config, log_config = a_base_config()
    return WeatherPlotServiceConfig(database_config, plot_config, log_config)


def prepare_directories():
    if os.path.isdir(file_directory()):
        shutil.rmtree(file_directory(), ignore_errors=False)

    os.makedirs(file_directory(), exist_ok=True)


class TestDatabaseConfigSection(unittest.TestCase):
    def setUp(self):
        self._ini_file = configparser.ConfigParser()
        self._ini_file.optionxform = str

    def tearDown(self):
        pass

    def test_read_write_section_to_ini_file(self):
        # given:
        section_tag = "database"
        expected_config = a_weather_server_config().get_database_config()

        self._ini_file[section_tag] = {}

        # when:
        expected_config.write_section_to_ini_file(self._ini_file[section_tag])
        got_config = DatabaseConfigSection.read_section_from_ini_file(self._ini_file[section_tag])

        # then:
        self.assertEqual(got_config, expected_config)


class TestFTPReceiverConfigSection(unittest.TestCase):
    def setUp(self):
        self._ini_file = configparser.ConfigParser()
        self._ini_file.optionxform = str

    def tearDown(self):
        pass

    def test_read_write_section_to_ini_file(self):
        # given:
        section_tag = "receiver"
        expected_config = a_weather_server_config().get_ftp_receiver_settings()

        self._ini_file[section_tag] = {}

        # when:
        expected_config.write_section_to_ini_file(self._ini_file[section_tag])
        got_config = FTPReceiverConfigSection.read_section_from_ini_file(self._ini_file[section_tag])

        # then:
        self.assertEqual(got_config, expected_config)


class TestPlotConfigSection(unittest.TestCase):
    def setUp(self):
        self._ini_file = configparser.ConfigParser()
        self._ini_file.optionxform = str

    def tearDown(self):
        pass

    def test_read_write_section_to_ini_file(self):
        # given:
        section_tag = "plotter"
        expected_config = a_plotter_service_config().get_plotter_settings()

        self._ini_file[section_tag] = {}

        # when:
        expected_config.write_section_to_ini_file(self._ini_file[section_tag])
        got_config = PlotConfigSection.read_section_from_ini_file(self._ini_file[section_tag])

        # then:
        self.assertEqual(got_config, expected_config)


class TestLogConfigSection(unittest.TestCase):
    def setUp(self):
        self._ini_file = configparser.ConfigParser()
        self._ini_file.optionxform = str

    def tearDown(self):
        pass

    def test_read_write_section_to_ini_file(self):
        # given:
        section_tag = "plotter"
        expected_config = a_weather_server_config().get_log_config()

        self._ini_file[section_tag] = {}

        # when:
        expected_config.write_section_to_ini_file(self._ini_file[section_tag])
        got_config = LogConfigSection.read_section_from_ini_file(self._ini_file[section_tag])

        # then:
        self.assertEqual(got_config, expected_config)


class TestFTPWeatherServerIniFile(unittest.TestCase):
    def setUp(self):
        prepare_directories()

    def tearDown(self):
        pass

    def test_read_write_ini_file(self):
        # given:
        ini_file_config = FTPWeatherServerIniFile(ini_file_name())
        expected_config = a_weather_server_config()

        # when:
        ini_file_config.write(expected_config)
        got_config = ini_file_config.read()

        # then:
        self.assertEqual(got_config, expected_config)


class TestWeatherPlotServiceIniFile(unittest.TestCase):
    def setUp(self):
        prepare_directories()

    def tearDown(self):
        pass

    def test_read_write_ini_file(self):
        # given:
        ini_file_config = WeatherPlotServiceIniFile(ini_file_name())
        expected_config = a_plotter_service_config()

        # when:
        ini_file_config.write(expected_config)
        got_config = ini_file_config.read()

        # then:
        self.assertEqual(got_config, expected_config)


class TestIniFileUtils(unittest.TestCase):
    def setUp(self):
        prepare_directories()

    def tearDown(self):
        pass

    def test_check_section_for_all_tags(self):
        # given:
        required_tags = LogConfigSection._LOG_SUBSECTION
        ini_file_config = WeatherPlotServiceIniFile(ini_file_name())
        config = a_plotter_service_config()
        ini_file_config.write(config)

        # when:
        section = ini_file_config._get_section("log")
        got_check_result = IniFileUtils.check_section_for_all_tags(section, required_tags, is_root_level=False)

        # then:
        self.assertTrue(got_check_result)

    def test_check_section_for_all_tags_with_missing_tag(self):
        # given:
        required_tags = LogConfigSection._LOG_SUBSECTION[:]
        required_tags.append("FakeTag")
        ini_file_config = WeatherPlotServiceIniFile(ini_file_name())
        config = a_plotter_service_config()
        ini_file_config.write(config)

        # when:
        section = ini_file_config._get_section("log")
        got_check_result = IniFileUtils.check_section_for_all_tags(section, required_tags, is_root_level=False)

        # then:
        self.assertFalse(got_check_result)

if __name__ == '__main__':
    unittest.main()
