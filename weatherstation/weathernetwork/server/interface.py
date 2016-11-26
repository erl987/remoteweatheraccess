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
        pass


class IDatabaseService(metaclass=ABCMeta):
    """Interface class for weather database services"""

    @abstractmethod
    def add_data(self, message):
        pass

    @abstractmethod
    def register_observer(self, observer):
        pass

    @abstractmethod
    def unregister_observer(self, observer):
        pass


class IDatabaseServiceFactory(metaclass=ABCMeta):
    """Abstract factory for weather database services"""

    @abstractmethod
    def create(self, use_logging):
        pass


class IIniConfigSection(metaclass=ABCMeta):
    """Interface class for server configuration data compatible to INI-files."""

    @staticmethod
    @abstractmethod
    def read_section_from_ini_file(section):
        pass

    @abstractmethod
    def write_section_to_ini_file(self, config_file_section):
        pass
