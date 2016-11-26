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
