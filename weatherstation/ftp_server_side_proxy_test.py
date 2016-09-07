import unittest
from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory
from multiprocessing import Queue

class FTPServerSideProxy_test(unittest.TestCase):
    def setUp(self):
        """Sets up each unit test."""
        db_file_name = "data/weather.db"
        self._existing_data_directory = "C:\\Users\\Ralf\\Documents\\test"
        self._not_existing_data_directory = "" # this a non-existing fake directory
        self._temp_data_directory = "C:\\Users\\Ralf\\Documents\\test\\temp"
        self._data_file_extension = ".ZIP"

        self._sql_database_service_factory = SQLDatabaseServiceFactory(db_file_name)
        self._exception_queue = Queue()


    def tearDown(self):
        """Finishes each unit test."""

    def _on_message(self, message):
        print(message.get_message())

    def test(self): # TODO: implement the test
        with FTPServerSideProxy(self._sql_database_service_factory, self._existing_data_directory, self._data_file_extension, self._temp_data_directory, self._on_message, self._exception_queue) as proxy:
            pass
            ## stall the main thread until the program is finished
            #exception_from_subprocess = []
            #try:
            #    exception_from_subprocess = self._exception_queue.get()
            #except KeyboardInterrupt:
            #    pass

            #if exception_from_subprocess:
            #    exception_from_subprocess.re_raise()   


    def test_invalid_data_file(self):
        with self.assertRaises(IOError):
            with FTPServerSideProxy(self._sql_database_service_factory, self._not_existing_data_directory, self._data_file_extension, self._temp_data_directory, self._on_message, self._exception_queue) as proxy:
                # stall the main thread until the program is finished
                exception_from_subprocess = []
                try:
                    exception_from_subprocess = self._exception_queue.get()
                except KeyboardInterrupt:
                    pass

                if exception_from_subprocess:
                    exception_from_subprocess.re_raise()        


if __name__ == '__main__':
    unittest.main()
