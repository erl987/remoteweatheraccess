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

from abc import ABCMeta, abstractmethod


class IServerSideProxy(metaclass=ABCMeta):
    """Interface class for a weather server broker proxy"""
    @abstractmethod
    def acknowledge_persistence(self, finished_id, logger):
        """
        Performs the acknowledgement of a successful finished message transfer to the client

        :param finished_id:     id of the finished message
        :type finished_id:      int
        :param logger:          logging system of the server
        :type logger:           common.logging.IMultiProcessLogger
        """
        pass


class IDatabaseService(metaclass=ABCMeta):
    """Interface class for weather database services"""

    @abstractmethod
    def add_data(self, message):
        """
        Adds a dataset to the database.
        Note: Logging is only supported if the method is called from another than the main process.
        If already data exists for the requested station and timepoint, it is replaced silently if this operation
        is unambiguous.

        :param message:                 weather data message to be stored
        :type message:                  common.datastructures.WeatherMessage
        :raise NotExistingError:        if a requested station or sensor ID is not existing in the database
        :raise AlreadyExistingError:    if a dataset is already existing in the database for the given station,
                                        time or sensor ID and the replacement would be ambiguous, in that case the
                                        database remains unchanged
        """
        pass

    @abstractmethod
    def register_observer(self, observer):
        """
        Registers a new observer.

        :param observer:                observer object to be registered
        :type observer:                 server.interface.IServerSideProxy
        """
        pass

    @abstractmethod
    def unregister_observer(self, observer):
        """
        Unregisters an observer.

        :param observer:                observer object to be removed
        :type observer:                 server.interface.IServerSideProxy
        """
        pass


class IDatabaseServiceFactory(metaclass=ABCMeta):
    """Abstract factory for weather database services"""

    @abstractmethod
    def create(self, use_logging):
        """
        Creates a class instance.
        Note: If that instance is created with an active logger connection, it must not be executed on the main process.

        :param use_logging:             flag stating if that instance should contain a connection to the main logger
        :type use_logging:              bool
        :return:                        new class instance
        :rtype:                         SQLDatabaseService
        """
        pass


class IIniConfigSection(metaclass=ABCMeta):
    """Interface class for server configuration data compatible to INI-files."""

    @staticmethod
    @abstractmethod
    def read_section_from_ini_file(section):
        """
        Reads the database section of the INI-file.

        :param section:                 section containing the SQL-database configuration
        :type section:                  configparser.SectionProxy
        :return:                        database configuration
        :rtype:                         DatabaseConfigSection
        :raise InvalidConfigFileError:  if an entry in the given section is invalid
        """
        pass

    @abstractmethod
    def write_section_to_ini_file(self, config_file_section):
        """
        Writes the content of the object to a INI-file section.

        :param config_file_section:     section to contain the SQL-database configuration after that method call
        :type config_file_section:      configparser.ConfigParser
        """
        pass
