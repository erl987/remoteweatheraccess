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
from pathlib import Path

from weathernetwork.server.exceptions import InvalidConfigFileError
from weathernetwork.server.interface import IIniConfigSection


class BaseWeatherServerConfig(object):
    """Base class for configuration data on the weather server."""

    def __init__(self, database_config, log_config):
        """
        Constructor.

        :param database_config:         SQL-database configuration
        :type database_config:          DatabaseConfigSection
        :param log_config:              log system configuration. If empty, the default log system of the OS will be
                                        used.
        :type log_config:               LogConfigSection
        """
        self._database_config = database_config
        self._log_config = log_config

    def get_database_config(self):
        """
        Obtains the SQL-database configuration.

        :return:                        SQL-database configuration
        :rtype:                         DatabaseConfigSection
        """
        return self._database_config

    def get_log_config(self):
        """Obtains the log system configuration.

        :return:                        configuration of the log system. If empty, the default log system of the OS will
                                        be used.
        :rtype:                         LogConfigSection
        """
        return self._log_config


class FTPWeatherServerConfig(BaseWeatherServerConfig):
    """Configuration data of a FTP weather server"""

    def __init__(self, database_config, ftp_receiver_config, log_config):
        """
        Constructor.

        :param database_config:         SQL-database configuration
        :type database_config:          DatabaseConfigSection
        :param ftp_receiver_config:     FTP-based weather server configuration
        :type ftp_receiver_config:      FTPReceiverConfigSection
        :param log_config:              log system configuration. If empty, the default log system of the OS will be
                                        used.
        :type log_config:               LogConfigSection
        """
        super().__init__(database_config, log_config)
        self._ftp_receiver_config = ftp_receiver_config

    def get_ftp_receiver_settings(self):
        """
        Obtains the FTP-based weather server configuration.

        :return:                        configuration of the FTP-based weather server
        :rtype:                         FTPReceiverConfigSection
        """
        return self._ftp_receiver_config


class WeatherPlotServiceConfig(BaseWeatherServerConfig):
    """Configuration data of the weather plotter tool"""

    def __init__(self, database_config, plotter_config, log_config):
        """
        Constructor.

        :param database_config:         SQL-database configuration
        :type database_config:          DatabaseConfigSection
        :param plotter_config:          plotter configuration
        :type plotter_config:           PlotConfigSection
        :param log_config:              log system configuration. If empty, the default log system of the OS will be
                                        used.
        :type log_config:               LogConfigSection
        """
        super().__init__(database_config, log_config)
        self._plotter_config = plotter_config

    def get_plotter_settings(self):
        """
        Obtains the plotter configuration.

        :return:                        configuration of the FTP-based weather server
        :rtype:                         PlotConfigSection
        """
        return self._plotter_config


class DatabaseConfigSection(IIniConfigSection):
    """Configuration part for the SQLite-database."""

    # INI-file subsection tags
    _DB_FILE_NAME = "DatabaseFile"
    _DATABASE_SUBSECTION = [_DB_FILE_NAME]

    def __init__(self, db_file_name):
        """
        Constructor.

        :param db_file_name:            file name of the SQLite-database file
        :type db_file_name:             string
        """
        self._db_file_name = db_file_name

    def get_db_file_name(self):
        """
        Obtains the name of the SQL-database file.

        :return:                        file name of the SQLite-database file
        :rtype:                         string
        """
        return self._db_file_name

    @staticmethod
    def read_section_from_ini_file(section):
        """
        Reads the database section of the INI-file.

        :param section:                 section containing the SQL-database configuration
        :type section:                  configparser.SectionProxy
        :return:                        database configuration
        :rtype:                         DatabaseConfigSection
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        if not IniFileUtils.check_section_for_all_tags(section, DatabaseConfigSection._DATABASE_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        db_file_name = section.get(DatabaseConfigSection._DB_FILE_NAME)

        return DatabaseConfigSection(db_file_name)

    def write_section_to_ini_file(self, config_file_section):
        """
        Writes the content of the object to a INI-file section.

        :param config_file_section:     section to contain the SQL-database configuration after that method call
        :type config_file_section:      configparser.ConfigParser
        """
        config_file_section[DatabaseConfigSection._DB_FILE_NAME] = self.get_db_file_name()


class FTPReceiverConfigSection(object):
    """Configuration part for the FTP-based weather server."""

    # INI-file subsection tags
    _RECEIVER_DIRECTORY = "ReceiverDirectory"
    _TEMP_DIRECTORY = "TempDirectory"
    _DATA_FILE_EXTENSION = "DataFileExtension"
    _TIME_BETWEEN_DATA = "TimeBetweenData"
    _RECEIVER_SUBSECTION = [_RECEIVER_DIRECTORY, _TEMP_DIRECTORY, _DATA_FILE_EXTENSION, _TIME_BETWEEN_DATA]

    def __init__(self, receiver_directory, temp_data_directory, data_file_extension, time_between_data):
        """
        Constructor.

        :param receiver_directory:      root of the directories where the FTP-server saves new data files (in one
                                        subdirectory for each station)
        :type receiver_directory:       string
        :param temp_data_directory:     temporary data directory available for the server for processing the new data
                                        files
        :type temp_data_directory:      string
        :param data_file_extension:     file extension of the data files, may contain a leading dot (typically: ZIP)
        :type data_file_extension:      string
        :param time_between_data:       time between two timepoints in the datafiles (only used for the first timepoint
                                        in a file), in minutes
        :type time_between_data:        float
        """
        self._receiver_directory = receiver_directory
        self._temp_data_directory = temp_data_directory

        if not data_file_extension.startswith("."):
            data_file_extension = "." + data_file_extension
        self._data_file_extension = data_file_extension.upper()

        self._time_between_data = time_between_data

    def get(self):
        """
        Obtains the complete configuration data for the FTP-based weather server.

        :return:                        root of the directories where the FTP-server saves new data files (in one
                                        subdirectory for each station)
        :rtype:                         string
        :return:                        temporary data directory available for the server for processing the new data
                                        files
        :rtype:                         string
        :return:                        file extension of the data files, may contain a leading dot (typically: ZIP)
        :rtype:                         string
        :return:                        time between two timepoints in the datafiles (only used for the first timepoint
                                        in a file), in minutes
        :rtype:                         float
        """
        return self._receiver_directory, self._temp_data_directory, self._data_file_extension, self._time_between_data

    @staticmethod
    def read_section_from_ini_file(section):
        """
        Reads the receiver section of the INI-file.

        :param section:                 section containing the FTP-based weather server configuration
        :type section:                  ConfigParser
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        if not IniFileUtils.check_section_for_all_tags(section, FTPReceiverConfigSection._RECEIVER_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        receiver_directory = section.get(FTPReceiverConfigSection._RECEIVER_DIRECTORY)
        temp_data_directory = section.get(FTPReceiverConfigSection._TEMP_DIRECTORY)
        data_file_extension = section.get(FTPReceiverConfigSection._DATA_FILE_EXTENSION)
        time_between_data = section.getfloat(FTPReceiverConfigSection._TIME_BETWEEN_DATA)

        return FTPReceiverConfigSection(receiver_directory, temp_data_directory, data_file_extension, time_between_data)

    def write_section_to_ini_file(self, config_file_section):
        """
        Writes the content of the object to a INI-file section.

        :param config_file_section:     section to contain the FTP-based weather server configuration after that method
                                        call
        :type config_file_section:      ConfigParser
        """
        receiver_directory, temp_data_directory, data_file_extension, time_between_data = self.get()
        config_file_section[FTPReceiverConfigSection._RECEIVER_DIRECTORY] = receiver_directory
        config_file_section[FTPReceiverConfigSection._TEMP_DIRECTORY] = temp_data_directory
        config_file_section[FTPReceiverConfigSection._DATA_FILE_EXTENSION] = data_file_extension
        config_file_section[FTPReceiverConfigSection._TIME_BETWEEN_DATA] = str(time_between_data)


class PlotConfigSection(IIniConfigSection):
    """Configuration part for the weather data plotting"""

    # INI-file subsection tags
    _SENSORS_TO_PLOT = "SensorsToPlot"
    _GRAPH_DIRECTORY = "PlotDirectory"
    _GRAPH_FILE_NAME = "PlotFileName"
    _TIME_PERIOD_DURATION = "NumberOfDaysToPlot"
    _PLOTTER_SUBSECTION = [_SENSORS_TO_PLOT, _GRAPH_DIRECTORY, _GRAPH_FILE_NAME, _TIME_PERIOD_DURATION]

    def __init__(self, sensors_to_plot, graph_directory, graph_file_name, time_period_duration):
        """
        Constructor.

        :param sensors_to_plot:         sensors to be plotted (format: [('baseStation', 'pressure'), ...])
        :type sensors_to_plot:          list of tuple
        :param graph_directory:         base directory of the plots, the files are stored in a subdirectory named after
                                        the station ID
        :type graph_directory:          string
        :param graph_file_name:         name of the graph files
        :type graph_file_name:          string
        :param time_period_duration:    plotting period in days (starting with the latest data, going back N days)
        :type time_period_duration:     int
        """
        self._sensors_to_plot = sensors_to_plot
        self._graph_directory = graph_directory
        self._graph_file_name = graph_file_name
        self._time_period_duration = time_period_duration

    def get_graph_file_settings(self):
        """
        Obtains the graph file settings.

        :return:                        graph output base directory, graph file name
        :rtype:                         string, string
        """
        return self._graph_directory, self._graph_file_name

    def get_sensors_to_plot(self):
        """
        Obtains the sensors to be plotted.

        :return:                        sensors to be plotted (format: ('OUT1', 'temperature'), ('OUT1', 'humidity')])
        :rtype:                         list of tuple
        """
        return self._sensors_to_plot

    def get_time_period_duration(self):
        """
        Obtains the plotting time period.

        :return:                        plotting period in days (starting with the latest data, going back N days)
        :rtype:                         int
        """
        return self._time_period_duration

    @staticmethod
    def _strip_sensor_name(sensor_name):
        """
        Checks a sensor name for validity and strips all leading and trailing spaces.

        :param sensor_name:                 name of the sensor to be checked
        :type sensor_name:                  string
        :return:                            sensor name stripped from leading and trailing spaces
        :rtype:                             string
        :raise InvalidConfigFileException:  if the sensor name is invalid
        """
        if '(' in sensor_name or ')' in sensor_name or ',' in sensor_name:
            raise InvalidConfigFileError("Sensor name was not correctly parsed, it contains invalid characters.")

        return sensor_name.strip()

    @staticmethod
    def _parse_sensors_string(sensors_string):
        """
        Parses the INI-file entry for the definition of the sensors to be plotted.

        :param sensors_string:          string from the INI-file containing the sensors to be plotted
        :type sensors_string:           string
        :return:                        parsed sensors to be plotted (format: [('rain', 'cumulated'), ...])
        :rtype:                         list of tuple
        :raise InvalidConfigFileError:  if the parsed sensor string is invalid
        """
        try:
            splitted_sensors_string = sensors_string.split(',')

            # reconcatenate all combined sensor definitions of the type "(main, sub)"
            sensors_info = []
            for item in splitted_sensors_string[:]:
                item = item.strip()
                if not item.endswith(')'):
                    sensors_info.append(item)
                else:
                    sensors_info[-1] += ',' + item

            # parse the definition for each sensor
            sensors_to_plot = []
            for sensor in sensors_info:
                if sensor.startswith('(') and sensor.endswith(')'):
                    sensor = sensor.replace('(', '')
                    sensor = sensor.replace(')', '')
                    splitted_sensor_definition = sensor.split(',')
                    if len(splitted_sensor_definition) != 2:
                        raise InvalidConfigFileError("A subsensor definition is invalid.")
                    sensors_to_plot.append(
                        (PlotConfigSection._strip_sensor_name(splitted_sensor_definition[0]),
                         PlotConfigSection._strip_sensor_name(splitted_sensor_definition[1]))
                    )
                else:
                    sensors_to_plot.append(PlotConfigSection._strip_sensor_name(sensor))
        except Exception:
            raise InvalidConfigFileError("Definition of the sensors to be plotted is invalid.")

        return sensors_to_plot

    @staticmethod
    def read_section_from_ini_file(section):
        """
        Reads the plotting configuration section of the INI-file.

        :param section:                 section containing the plotter configuration
        :type section:                  configparser.SectionProxy
        :return:                        the read section
        :rtype:                         PlotConfigSection
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        if not IniFileUtils.check_section_for_all_tags(section, PlotConfigSection._PLOTTER_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        sensors_to_plot = PlotConfigSection._parse_sensors_string(section.get(PlotConfigSection._SENSORS_TO_PLOT))
        graph_directory = section.get(PlotConfigSection._GRAPH_DIRECTORY)
        graph_file_name = section.get(PlotConfigSection._GRAPH_FILE_NAME)
        time_period_duration = section.getint(PlotConfigSection._TIME_PERIOD_DURATION)

        return PlotConfigSection(sensors_to_plot, graph_directory, graph_file_name, time_period_duration)

    def write_section_to_ini_file(self, config_file_section):
        """
        Writes the content of the object to a INI-file section.

        :param config_file_section:     section to contain the FTP-based weather server configuration after that method
                                        call
        :type config_file_section:      configparser.SectionProxy
        """
        graph_directory, graph_file_name = self.get_graph_file_settings()
        sensors_to_plot_string = str(self.get_sensors_to_plot())
        sensors_to_plot_string = sensors_to_plot_string.replace('\'', '')

        # removing the leading and trailing brackets in the string
        config_file_section[PlotConfigSection._SENSORS_TO_PLOT] = sensors_to_plot_string[1:-1]

        config_file_section[PlotConfigSection._GRAPH_DIRECTORY] = graph_directory
        config_file_section[PlotConfigSection._GRAPH_FILE_NAME] = graph_file_name
        config_file_section[PlotConfigSection._TIME_PERIOD_DURATION] = str(self.get_time_period_duration())


class LogConfigSection(IIniConfigSection):
    """Configuration part for the logging system."""

    # INI-file subsection tags
    _LOG_FILE = "LogFile"
    _MAX_KBYTES = "MaxLogFileSize"
    _NUM_FILES_TO_KEEP = "NumFilesToKeep"
    _LOG_SUBSECTION = [_LOG_FILE, _MAX_KBYTES, _NUM_FILES_TO_KEEP]

    def __init__(self, log_file_name, max_kbytes_per_file, num_files_to_keep):
        """
        Constructor.

        :param log_file_name:           nme of the log file
        :type log_file_name:            string
        :param max_kbytes_per_file:     maximum size of a log file (in KB). Larger files are renamed to ".1" ... by
                                        log rotation and a new file is started.
        :type max_kbytes_per_file:      int
        :param num_files_to_keep:       maximum number of log files kept. If set to 0, no file is deleted.
        :type num_files_to_keep:        int
        """
        self._log_file_name = log_file_name
        self._max_kbytes_per_file = max_kbytes_per_file
        self._num_files_to_keep = int(num_files_to_keep)

    def get_log_file_name(self):
        """
        Obtains the log file name.

        :return:                        log file name
        :rtype:                         string
        """
        return self._log_file_name

    def get_max_kbytes_per_files(self):
        """
        Obtains the maximum size of a log file.

        :return:                        maximum size of a log file (in KB). Larger files are renamed to ".1" ... by
                                        log rotation and a new file is started.
        :rtype:                         int
        """
        return self._max_kbytes_per_file

    def get_num_files_to_keep(self):
        """
        Obtains the maximum number of log files kept.

        :return:                        maximum number of log files kept. If set to 0, no file is deleted.
        :rtype:                         int
        """
        return self._num_files_to_keep

    @staticmethod
    def read_section_from_ini_file(section):
        """
        Reads the log section of the INI-file.

        :param section:                 section containing the log system configuration
        :type section:                  configparser.SectionProxy
        :return:                        the read section
        :rtype:                         LogConfigSection
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        if not IniFileUtils.check_section_for_all_tags(section, LogConfigSection._LOG_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        log_file_name = section.get(LogConfigSection._LOG_FILE)
        max_kbytes_per_file = section.getint(LogConfigSection._MAX_KBYTES)
        num_files_to_keep = section.getint(LogConfigSection._NUM_FILES_TO_KEEP)

        return LogConfigSection(log_file_name, max_kbytes_per_file, num_files_to_keep)

    def write_section_to_ini_file(self, config_file_section):
        """
        Writes the content of the object to a INI-file section.

        :param config_file_section:     section to contain the log system configuration after that method call
        :type config_file_section:      ConfigParser
        """
        config_file_section[LogConfigSection._LOG_FILE] = self.get_log_file_name()
        config_file_section[LogConfigSection._MAX_KBYTES] = str(self.get_max_kbytes_per_files())
        config_file_section[LogConfigSection._NUM_FILES_TO_KEEP] = str(self.get_num_files_to_keep())


class BaseWeatherServerIniFile(object):
    """Base class for weather server INI-files."""

    # INI-file main section tags
    _DATABASE_SECTION_TAG = "database"
    _LOG_SECTION_TAG = "log"
    _BASE_SECTIONS = [_DATABASE_SECTION_TAG, _LOG_SECTION_TAG]

    # common detail of the INI-file log section
    _IS_DEFAULT_OS_LOG = "DefaultOSLog"
    _LOG_SUBSECTION_BASE = [_IS_DEFAULT_OS_LOG]

    def __init__(self, file_name):
        """
        Constructor.

        :param file_name:               name of the INI config file.
        :type file_name:                string
        """
        if not Path(file_name).is_file():
            raise InvalidConfigFileError("The file '{}' does not exist".format(file_name))

        self._config_file = configparser.ConfigParser()
        self._file_name = file_name
        self._old_optionxform = None

    def get_section(self, section_name):
        """
        Obtains a section from the INI-configuration file.

        :param section_name:            name of the section to be retrieved
        :type section_name:             string
        :return:                        section
        :rtype:                         configparser.SectionProxy
        """
        return self._config_file[section_name]

    def read(self):
        """
        Reads the basic config data from the INI-file.

        :return:                        read basic config data
        :rtype:                         BaseWeatherServerConfig
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        self._config_file.clear()
        self._config_file.read(self._file_name)
        if not IniFileUtils.check_section_for_all_tags(
                self._config_file, BaseWeatherServerIniFile._BASE_SECTIONS, True):
            raise InvalidConfigFileError("At least one section header is invalid.")

        try:
            database_config = DatabaseConfigSection.read_section_from_ini_file(
                self._config_file[BaseWeatherServerIniFile._DATABASE_SECTION_TAG])

            log_section = self._config_file[BaseWeatherServerIniFile._LOG_SECTION_TAG]
            if not IniFileUtils.check_section_for_all_tags(
                    log_section, BaseWeatherServerIniFile._LOG_SUBSECTION_BASE, False):
                raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % log_section.name)
            is_default_os_log = log_section.getboolean(BaseWeatherServerIniFile._IS_DEFAULT_OS_LOG)
            if not is_default_os_log:
                log_config = LogConfigSection.read_section_from_ini_file(
                    self._config_file[BaseWeatherServerIniFile._LOG_SECTION_TAG])
            else:
                log_config = None
        except Exception as e:
            raise InvalidConfigFileError("Error parsing the config file: %s" % str(e))

        return BaseWeatherServerConfig(database_config, log_config)

    def prepare_writing(self):
        """
        Prepares the class for writing a INI-file.
        This method MUST be called by any child before writing to the INI-file.
        """
        self._config_file.clear()

        # changing the config file handler to maintain the case of the letters
        self._old_optionxform = self._config_file.optionxform
        self._config_file.optionxform = str

    def finish_writing(self):
        """
        Finishes writing to the INI-file.
        This method MUST be called by any child after writing to the INI-file.
        """
        with open(self._file_name, 'w') as file:
            self._config_file.write(file)

        # reset the original behaviour of the config file handler
        self._config_file.optionxform = self._old_optionxform

    def write(self, config):
        """
        Writes configuration data to the INI-file.

        :param config:                  configuration data to be written to the file represented by the object
        :type config:                   BaseWeatherServerConfig
        """
        # write the data to the configuration file
        self._config_file[BaseWeatherServerIniFile._DATABASE_SECTION_TAG] = {}
        self._config_file[BaseWeatherServerIniFile._LOG_SECTION_TAG] = {}
        config.get_database_config().write_section_to_ini_file(
            self._config_file[BaseWeatherServerIniFile._DATABASE_SECTION_TAG])

        log_config_section = self._config_file[BaseWeatherServerIniFile._LOG_SECTION_TAG]
        if config.get_log_config():
            log_config_section[BaseWeatherServerIniFile._IS_DEFAULT_OS_LOG] = "no"
            config.get_log_config().write_section_to_ini_file(log_config_section)
        else:
            log_config_section[BaseWeatherServerIniFile._IS_DEFAULT_OS_LOG] = "yes"

    def add_section(self, section_name):
        """
        Creates a new section of the INI-file and returns it.

        :param section_name:            name of the section to be created
        :type section_name:             string
        :return:                        created section
        :rtype:                         configparser.SectionProxy
        """
        self._config_file[section_name] = {}

        return self._config_file[section_name]


class FTPWeatherServerIniFile(BaseWeatherServerIniFile):
    """Config settings for a FTP weather server based on a INI-file."""

    # INI-file main section tags (specific to the present class)
    _RECEIVER_SECTION_TAG = "receiver"
    _MAIN_SECTIONS = [_RECEIVER_SECTION_TAG]

    def __init__(self, file_name):
        """
        Constructor.

        :param file_name:               name of the INI config file.
        :type file_name:                string
        """
        super().__init__(file_name)

    def read(self):
        """Reads the config data from the INI-file.

        :return:                        the read config data
        :rtype:                         FTPWeatherServerConfig
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        base_config = super().read()

        try:
            ftp_receiver_config = FTPReceiverConfigSection.read_section_from_ini_file(super().get_section(
                FTPWeatherServerIniFile._RECEIVER_SECTION_TAG))
        except Exception as e:
            raise InvalidConfigFileError("Error parsing the config file: %s" % str(e))

        return FTPWeatherServerConfig(
            base_config.get_database_config(),
            ftp_receiver_config,
            base_config.get_log_config())

    def write(self, config):
        """
        Writes configuration data to the INI-file.

        :param config:                  configuration data to be written to the file represented by the object
        :type config:                   FTPWeatherServerConfig
        """
        super().prepare_writing()
        super().write(config)
        config.get_ftp_receiver_settings().write_section_to_ini_file(super().add_section(
            FTPWeatherServerIniFile._RECEIVER_SECTION_TAG))
        super().finish_writing()


class WeatherPlotServiceIniFile(BaseWeatherServerIniFile):
    """Config settings for a weather plotter based on a INI-file."""

    # INI-file main section tags (specific to the present class)
    _PLOTTER_SECTION_TAG = "plotter"
    _MAIN_SECTIONS = [_PLOTTER_SECTION_TAG]

    def __init__(self, file_name):
        """
        Constructor.

        :param file_name:               name of the INI config file.
        :type file_name:                string
        """
        super().__init__(file_name)

    def read(self):
        """Reads the config data from the INI-file.

        :return:                        the read config data
        :rtype:                         WeatherPlotServiceConfig
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        base_config = super().read()

        try:
            plotter_config = PlotConfigSection.read_section_from_ini_file(super().get_section(
                WeatherPlotServiceIniFile._PLOTTER_SECTION_TAG))
        except Exception as e:
            raise InvalidConfigFileError("Error parsing the config file: %s" % str(e))

        return WeatherPlotServiceConfig(base_config.get_database_config(), plotter_config, base_config.get_log_config())

    def write(self, config):
        """
        Writes configuration data to the INI-file.

        :param config:                  configuration data to written to the file represented by the object
        :type config:                   WeatherPlotServiceConfig
        """
        super().prepare_writing()
        super().write(config)
        config.get_plotter_settings().write_section_to_ini_file(super().add_section(
            WeatherPlotServiceIniFile._PLOTTER_SECTION_TAG))
        super().finish_writing()


class IniFileUtils(object):
    """Utils methods for processing INI-configuration files."""
    @staticmethod
    def check_section_for_all_tags(section, required_tags, is_root_level):
        """
        Checks if the given section contains all required tags.

        :param section:                 section of the INI-file to be checked
        :type section:                  configparser.SectionProxy
        :param required_tags:           required tags for that section
        :type required_tags:            list of strings
        :param is_root_level:           flag stating if the root level is checked
        :type is_root_level:            boolean
        :return:                        True if the section contains all required tags
        :rtype:                         boolean
        """
        available_tags = list(section.keys())
        if not is_root_level:
            available_tags = [tag.lower() for tag in available_tags]
            required_tags = [tag.lower() for tag in required_tags]

        return set(required_tags) <= set(available_tags)
