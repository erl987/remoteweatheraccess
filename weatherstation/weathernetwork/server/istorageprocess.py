from abc import ABCMeta, abstractmethod

class IStorageProcess(metaclass=ABCMeta):
    """Interface for the persistence operation class"""

    @abstractmethod
    def storage_worker(self, db_file_name, data_queue, on_finished_connection, exception_handler):
        pass


