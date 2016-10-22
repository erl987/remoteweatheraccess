import configparser
from weathernetwork.server.exceptions import InvalidConfigFileError

class FTPWeatherServerConfig(object):
    """Configuration data of a FTP weather server"""

    def __init__(self, database_config, ftp_receiver_config, log_config):
        """ Constructor.

        :param database_config:         SQL-database configuration
        :type database_config:          DatabaseConfig object
        :param ftp_receiver_config:     FTP-based wather server configuration
        :type ftp_receiver_config:      FTPReceiverConfig object
        :param log_config:              log system configuration. If empty, the default log system of the OS will be used.
        :type log_config:               LogConfig object
        """
        self._database_config = database_config
        self._ftp_receiver_config = ftp_receiver_config
        self._log_config = log_config


    def get_database_config(self):
        """Obtains the SQL-database configuration.

        :return:                        SQL-database configuration
        :rtype:                         DatabaseConfig object
        """
        return self._database_config


    def get_ftp_receiver_settings(self):
        """Obtains the FTP-based weather server configuration.

        :return:                        configuration of the FTP-based weather server
        :rtype:                         FTPReceiverConfig object
        """
        return self._ftp_receiver_config


    def get_log_config(self):
        """Obtains the log system configuration.

        :return:                        configuration of the log system. If empty, the default log system of the OS will be used.
        :rtype:                         LogConfig object
        """
        return self._log_config


class DatabaseConfig(object):
    """Configuration of the SQLite-database."""

    def __init__(self, db_file_name):
        """Constructor.

        :param db_file_name:            file name of the SQLite-database file
        :type db_file_name:             string
        """
        self._db_file_name = db_file_name

    def get_db_file_name(self):
        """Obtains the name of the SQL-database file.

        :return:                        file name of the SQLite-database file
        :rtype:                         string
        """
        return self._db_file_name


class FTPReceiverConfig(object):
    """Configuration of the FTP-based weather server."""

    def __init__(self, receiver_directory, temp_data_directory, data_file_extension, time_between_data):
        """Constructor.

        :param receiver_directory:      root of the directories where the FTP-server saves new data files (in one subdirectory for each station)
        :type receiver_directory:       string
        :param temp_data_directory:     temporary data directory available for the server for processing the new data files
        :type temp_data_directory:      string
        :param data_file_extension:     file extension of the data files, may contain a leading dot (typically: ZIP)
        :type data_file_extension:      string
        :param time_between_data:       time between two timepoints in the datafiles (only used for the first timepoint in a file), in minutes
        :type time_between_data:        float
        """
        self._receiver_directory = receiver_directory
        self._temp_data_directory = temp_data_directory
        
        if not data_file_extension.startswith("."):
            data_file_extension = "." + data_file_extension
        self._data_file_extension = data_file_extension

        self._time_between_data = time_between_data


    def get(self):
        """Obtains the complete configuration data for the FTP-based weather server.

        :return:                        root of the directories where the FTP-server saves new data files (in one subdirectory for each station)
        :rtype:                         string
        :return:                        temporary data directory available for the server for processing the new data files
        :rtype:                         string
        :return:                        file extension of the data files, may contain a leading dot (typically: ZIP)
        :rtype:                         string
        :return:                        time between two timepoints in the datafiles (only used for the first timepoint in a file), in minutes
        :rtype:                         float                     
        """
        return self._receiver_directory, self._temp_data_directory, self._data_file_extension, self._time_between_data


class LogConfig(object):
    """Configuration of the logging system."""

    def __init__(self, log_file_name, max_kbytes_per_file, num_files_to_keep):
        """Constructor.

        :param log_file_name:           nme of the log file
        :type log_file_name:            string
        :param max_kbytes_per_file:     maximum size of a log file (in KB). Larger files are renamed to ".1" ... by log rotation and a new file is started.
        :type max_kbytes_per_file:      int
        :param num_files_to_keep:       maximum number of log files kept. If set to 0, no file is deleted.
        :type num_files_to_keep:        int
        """
        self._log_file_name = log_file_name
        self._max_kbytes_per_file = max_kbytes_per_file
        self._num_files_to_keep = int(num_files_to_keep)


    def get_log_file_name(self):
        """Obtains the log file name.

        :return:                        log file name
        :rtype:                         string
        """
        return self._log_file_name


    def get_max_kbytes_per_files(self):
        """Obtains the maximum size of a log file.

        :return:                        maximum size of a log file (in KB). Larger files are renamed to ".1" ... by log rotation and a new file is started.
        :rtype:                         int
        """
        return self._max_kbytes_per_file
    

    def get_num_files_to_keep(self):
        """Obtains the maximum number of log files kept.

        :return:                        maximum number of log files kept. If set to 0, no file is deleted.
        :rtype:                         int
        """
        return self._num_files_to_keep


class FTPWeatherServerConfigFile(object):
    """Config settings for a FTP weather server based on a INI-file."""

    # INI-file tags
    DATABASE_SECTION_TAG = "database"
    DB_FILE_NAME = "DatabaseFile"
    DATABASE_SUBSECTION = [DB_FILE_NAME]

    RECEIVER_SECTION_TAG = "receiver"
    RECEIVER_DIRECTORY = "ReceiverDirectory"
    TEMP_DIRECTORY = "TempDirectory"
    DATA_FILE_EXTENSION = "DataFileExtension"
    TIME_BETWEEN_DATA = "TimeBetweenData"
    RECEIVER_SUBSECTION = [RECEIVER_DIRECTORY, TEMP_DIRECTORY, DATA_FILE_EXTENSION, TIME_BETWEEN_DATA]
    
    LOG_SECTION_TAG = "log"
    IS_DEFAULT_OS_LOG = "DefaultOSLog"
    LOG_FILE = "LogFile"
    MAX_KBYTES = "MaxLogFileSize"
    NUM_FILES_TO_KEEP = "NumFilesToKeep"
    LOG_SUBSECTION_MINIMUM = [IS_DEFAULT_OS_LOG] # only that entry is required
    LOG_SUBSECTION_OPTIONAL = [LOG_FILE, MAX_KBYTES, NUM_FILES_TO_KEEP] # only required if no default OS log is set

    MAIN_SECTIONS = [DATABASE_SECTION_TAG, RECEIVER_SECTION_TAG, LOG_SECTION_TAG]


    def __init__(self, file_name):
        """Constructor

        :param file_name:               name of the INI config file.
        :type file_name:                string
        """
        self._config_file = configparser.ConfigParser()
        self._file_name = file_name


    def _check_section_for_all_tags(self, section, required_tags, is_root_level):
        """Checks if the given section contains all required tags.

        :param section:                 section of the INI-file to be checked
        :type section:                  ConfigParser object
        :param required_tags:           required tags for that section
        :type required_tags:            list of strings
        :param is_root_level:           flag stating if the root level is checked (True, false otherwise)
        :type is_root_level:            boolean
        """
        available_tags = list(section.keys())
        if not is_root_level:
            available_tags = [tag.lower() for tag in available_tags]
            required_tags = [tag.lower() for tag in required_tags]
        
        return set(required_tags) <= set(available_tags)


    def read(self):
        """Reads the config data from the INI-file."""
        self._config_file.clear()
        self._config_file.read(self._file_name)
        if not self._check_section_for_all_tags(self._config_file, FTPWeatherServerConfigFile.MAIN_SECTIONS, True):
            raise InvalidConfigFileError("At least one section header is invalid.")

        try:
            database_config = self._read_database_section(self._config_file[FTPWeatherServerConfigFile.DATABASE_SECTION_TAG])
            ftp_receiver_config = self._read_ftp_receiver_section(self._config_file[FTPWeatherServerConfigFile.RECEIVER_SECTION_TAG])
            log_config = self._read_log_section(self._config_file[FTPWeatherServerConfigFile.LOG_SECTION_TAG])
        except Exception as e:
            raise InvalidConfigFileError("Error parsing the config file: %s" % str(e))

        return FTPWeatherServerConfig(database_config, ftp_receiver_config, log_config)


    def _read_database_section(self, section):
        """Reads the database section of the INI-file.

        :param section:                 section containing the SQL-database configuration
        :type section:                  ConfigParser object
        """
        if not self._check_section_for_all_tags(section, FTPWeatherServerConfigFile.DATABASE_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        db_file_name = section.get(FTPWeatherServerConfigFile.DB_FILE_NAME)  
        
        return DatabaseConfig(db_file_name)


    def _read_ftp_receiver_section(self, section):
        """Reads the receiver section of the INI-file.

        :param section:                 section containing the FTP-based weather server configuration
        :type section:                  ConfigParser object
        """
        if not self._check_section_for_all_tags(section, FTPWeatherServerConfigFile.RECEIVER_SUBSECTION, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        receiver_directory = section.get(FTPWeatherServerConfigFile.RECEIVER_DIRECTORY)
        temp_data_directory = section.get(FTPWeatherServerConfigFile.TEMP_DIRECTORY)
        data_file_extension = section.get(FTPWeatherServerConfigFile.DATA_FILE_EXTENSION)
        time_between_data = section.getfloat(FTPWeatherServerConfigFile.TIME_BETWEEN_DATA)

        return FTPReceiverConfig(receiver_directory, temp_data_directory, data_file_extension, time_between_data)


    def _read_log_section(self, section):
        """Reads the log section of the INI-file.
        
        :param section:                 section containing the log system configuration
        :type section:                  ConfigParser object
        """
        if not self._check_section_for_all_tags(section, FTPWeatherServerConfigFile.LOG_SUBSECTION_MINIMUM, False):
            raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

        is_default_OS_log = section.getboolean(FTPWeatherServerConfigFile.IS_DEFAULT_OS_LOG)
        if not is_default_OS_log:
            if not self._check_section_for_all_tags(section, FTPWeatherServerConfigFile.LOG_SUBSECTION_OPTIONAL, False):
                raise InvalidConfigFileError("An entry in the section \"%s\" is invalid." % section.name)

            log_file_name = section.get(FTPWeatherServerConfigFile.LOG_FILE)
            max_kbytes_per_file = section.getint(FTPWeatherServerConfigFile.MAX_KBYTES)
            num_files_to_keep = section.getint(FTPWeatherServerConfigFile.NUM_FILES_TO_KEEP)
            log_config = LogConfig(log_file_name, max_kbytes_per_file, num_files_to_keep)   
        else:
            log_config = None

        return log_config


    def write(self, config):
        """Writes configuration data to the INI-file.

        :param config:                  configuration data to written to the file represented by the object
        :type config:                   FTPWeatherServerConfig object
        """
        self._config_file.clear()

        # changing the config file handler to maintain the case of the letters
        old_optionxform = self._config_file.optionxform
        self._config_file.optionxform = str

        database_config = config.get_database_config()
        tag = FTPWeatherServerConfigFile.DATABASE_SECTION_TAG
        self._config_file[tag] = {}
        self._config_file[tag][FTPWeatherServerConfigFile.DB_FILE_NAME] = database_config.get_db_file_name()

        ftp_receiver_settings = config.get_ftp_receiver_settings()
        receiver_directory, temp_data_directory, data_file_extension, time_between_data = ftp_receiver_settings.get()
        tag = FTPWeatherServerConfigFile.RECEIVER_SECTION_TAG
        self._config_file[tag] = {}
        self._config_file[tag][FTPWeatherServerConfigFile.RECEIVER_DIRECTORY] = receiver_directory
        self._config_file[tag][FTPWeatherServerConfigFile.TEMP_DIRECTORY] = temp_data_directory
        self._config_file[tag][FTPWeatherServerConfigFile.DATA_FILE_EXTENSION] = data_file_extension
        self._config_file[tag][FTPWeatherServerConfigFile.TIME_BETWEEN_DATA] = str(time_between_data)

        log_config = config.get_log_config()
        tag = FTPWeatherServerConfigFile.LOG_SECTION_TAG
        self._config_file[tag] = {}
        if not log_config:
            self._config_file[tag][FTPWeatherServerConfigFile.IS_DEFAULT_OS_LOG] = "yes"
        else:
            self._config_file[tag][FTPWeatherServerConfigFile.IS_DEFAULT_OS_LOG] = "no"
            self._config_file[tag][FTPWeatherServerConfigFile.LOG_FILE] = log_config.get_log_file_name()
            self._config_file[tag][FTPWeatherServerConfigFile.MAX_KBYTES] = str(log_config.get_max_kbytes_per_files())
            self._config_file[tag][FTPWeatherServerConfigFile.NUM_FILES_TO_KEEP] = str(log_config.get_num_files_to_keep())

        with open(self._file_name, 'w') as file:
            self._config_file.write(file)

        # reset the original behaviour of the config file handler
        self._config_file.optionxform = old_optionxform