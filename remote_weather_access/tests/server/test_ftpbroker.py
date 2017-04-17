# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
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

import datetime
import os
import shutil
import threading
import time
import unittest
from functools import partial
from multiprocessing import Process, Queue

from watchdog.events import FileSystemEvent

from remote_weather_access.server.config import FTPReceiverConfigSection
from remote_weather_access.server.exceptions import NotExistingError
from remote_weather_access.common.datastructures import WeatherMessage
from remote_weather_access.common.datastructures import WeatherStationDataset
from remote_weather_access.server.interface import IDatabaseServiceFactory, IDatabaseService
from remote_weather_access.common.logging import MultiProcessConnector, IMultiProcessLogger
from remote_weather_access.server.ftpbroker import FileSystemObserver, FTPServerBrokerProcess, FTPBroker, \
    FTPServerSideProxyProcess, FTPServerSideProxy


def data_base_directory():
    return "./tests/workingDir/ftpbroker"


def data_directory():
    return data_base_directory() + os.sep + a_station_id()


def temp_directory():
    return data_base_directory() + os.sep + "temp"


def not_existing_data_directory():
    return "./tests/workingDir/notexisting"


def data_file_extension():
    return ".zip"


def a_station_id():
    return "TES2"


def another_station_id():
    return "TES"


def a_file_name():
    return "150315_213115_1345_" + a_station_id() + data_file_extension()


def a_file_path():
    return data_directory() + os.sep + a_file_name()


def a_path_of_invalid_file():
    return data_base_directory() + os.sep + another_station_id() + os.sep + "message_" + another_station_id() + \
           data_file_extension()


def create_a_data_file():
    shutil.copy("./tests/testdata" + os.sep + a_file_name(), a_file_path())


def prepare_directories():
    if os.path.isdir(data_directory()):
        shutil.rmtree(data_directory(), ignore_errors=False)
    os.makedirs(data_directory(), exist_ok=True)  # creates the directory if required
    os.makedirs(temp_directory(), exist_ok=True)


def _exception_handler(exception, queue):
    queue.put(exception)


def get_broker_settings():
    logging_queue = Queue()

    delta_time = 10
    combi_sensor_ids = ["OUT1"]
    combi_sensor_descriptions = {"OUT1": "outdoor sensor 1"}
    logging_connection = MultiProcessConnector(logging_queue, 0)

    return delta_time, combi_sensor_ids, combi_sensor_descriptions, logging_connection


class BrokerParentMock(object):
    def send_persistence_acknowledgement(self, message_id, logger):
        pass


class ProxyParentMock(object):
    def __init__(self, result_queue):
        self._result_queue = result_queue

    def acknowledge_persistence(self, message_id, logger):
        self._result_queue.put(message_id)
        logger.log(IMultiProcessLogger.INFO, "Acknowledging persistence")


class SQLDatabaseServiceMock(IDatabaseService):
    def get_combi_sensors(self):
        return ["OUT1"], {"OUT1": "outdoor sensor 1"}

    def __init__(self, result_queue, has_exception_throwing_add_data, has_exception_throwing_register):
        self._result_queue = result_queue
        self._has_exception_throwing_db = has_exception_throwing_add_data
        self._has_exception_throwing_register = has_exception_throwing_register

    def add_data(self, message):
        if self._has_exception_throwing_db:
            raise NotExistingError("Test exception from add data")
        else:
            self._result_queue.put(message)

    def register_observer(self, observer):
        if self._has_exception_throwing_register:
            raise NotExistingError("Test exception from the observer")

    def unregister_observer(self, observer):
        pass


class SQLDatabaseServiceFactoryMock(IDatabaseServiceFactory):
    def __init__(self, result_queue, use_db_throwing_on_add_data=False, use_db_throwing_on_register=False):
        self._database_service_mock = SQLDatabaseServiceMock(result_queue,
                                                             use_db_throwing_on_add_data,
                                                             use_db_throwing_on_register)

    def create(self, use_logging):
        return self._database_service_mock


class TestFileSystemObserver(unittest.TestCase):
    def setUp(self):
        self._exception = None
        self._received_file_queue = Queue()
        prepare_directories()

    def tearDown(self):
        pass

    def test_on_modified(self):
        # given:
        file_system_observer = FileSystemObserver(data_base_directory())
        file_system_observer.set_received_file_queue(self._received_file_queue)
        file_system_observer._processed_files_lock = threading.Lock()
        modified_event = FileSystemEvent(a_file_path())

        # when:
        file_system_observer.on_modified(modified_event)

        # then:
        got_filepath = self._received_file_queue.get(timeout=1.0)
        self.assertEqual(got_filepath, a_file_path())

    def test_process(self):
        # given:
        filesystem_observer = FileSystemObserver(data_base_directory())
        filesystem_observer_process = Process(
            target=filesystem_observer.process, args=(self._received_file_queue, _exception_handler)
        )
        try:
            filesystem_observer_process.start()
            time.sleep(2.0)  # significant waiting time is required to start the file watching reliably

            # when:
            create_a_data_file()
            got_filepath = self._received_file_queue.get(timeout=5.0)
            filesystem_observer.stop()

            # then:
            self.assertEqual(got_filepath, a_file_path())
        finally:
            filesystem_observer.stop()
            filesystem_observer_process.join()

    def test_process_exception_transfer(self):
        # given:
        exception_queue = Queue()
        filesystem_observer = FileSystemObserver(not_existing_data_directory())

        # when:
        filesystem_observer_process = Process(
            target=filesystem_observer.process, args=(self._received_file_queue,
                                                      partial(_exception_handler, queue=exception_queue))
        )
        try:
            filesystem_observer_process.start()
            got_exception = exception_queue.get(timeout=5.0)

            # then:
            self.assertRaises(IOError, got_exception.re_raise)
        finally:
            filesystem_observer_process.join()

    def test_feed_modified_file(self):
        # given:
        file_system_observer = FileSystemObserver(data_base_directory())
        file_system_observer.set_received_file_queue(self._received_file_queue)

        # when:
        file_system_observer.feed_modified_file(a_file_path())

        # then:
        got_filepath = self._received_file_queue.get()
        self.assertEqual(got_filepath, a_file_path())


class TestFTPServerBrokerProcess(unittest.TestCase):
    def setUp(self):
        self._received_file_queue = Queue()
        prepare_directories()

    def tearDown(self):
        pass

    def _create_broker_process(self):
        request_queue = Queue()
        exception_queue = Queue()

        parent = BrokerParentMock()
        delta_time, combi_sensor_ids, combi_sensor_descriptions, logging_connection = get_broker_settings()

        broker = FTPServerBrokerProcess(data_base_directory(), data_file_extension(), temp_directory(),
                                        delta_time, combi_sensor_ids, combi_sensor_descriptions)
        broker_process = Process(
            target=broker.process, args=(self._received_file_queue, request_queue, parent,
                                         logging_connection, partial(_exception_handler, queue=exception_queue))
        )
        return broker_process, request_queue, exception_queue

    def test_process(self):
        # given:
        broker_process, request_queue, exception_queue = self._create_broker_process()
        try:
            broker_process.start()

            # when:
            create_a_data_file()
            self._received_file_queue.put(a_file_path())
            got_message_id, got_station_id, got_data = request_queue.get(timeout=5.0)
            got_file_name = got_message_id  # the message id is identical to the file name

            # then:
            self.assertEqual(got_file_name, a_file_name())
            self.assertEqual(got_station_id, a_station_id())
            self.assertEqual(len(got_data), 2143)
        finally:
            self._received_file_queue.put(None)  # finish the process
            if broker_process.is_alive():
                broker_process.join()

    def test_process_exception_transfer(self):
        # given:
        broker_process, request_queue, exception_queue = self._create_broker_process()
        try:
            broker_process.start()

            # when:
            self._received_file_queue.put(a_path_of_invalid_file())
            got_exception = exception_queue.get(timeout=5.0)

            # then:
            self.assertRaises(FileNotFoundError, got_exception.re_raise)
        finally:
            self._received_file_queue.put(None)  # finish the process
            if broker_process.is_alive():
                broker_process.join()

    def test_get_station_id(self):
        # given:
        file_name_base, file_extension = os.path.splitext(a_file_name())

        # when:
        got_station_id = FTPServerBrokerProcess.get_station_id(file_name_base)

        # then:
        self.assertEqual(got_station_id, a_station_id())

    def test_get_station_id_empty_string(self):
        # given:
        file_name_base = ""

        # when:
        got_station_id = FTPServerBrokerProcess.get_station_id(file_name_base)

        # then:
        self.assertEqual(got_station_id, "")


class TestFTPBroker(unittest.TestCase):
    def setUp(self):
        prepare_directories()
        create_a_data_file()

    def tearDown(self):
        pass

    def test_ftpbroker(self):
        # given:
        request_queue = Queue()

        delta_time, combi_sensor_ids, combi_sensor_descriptions, logging_connection = get_broker_settings()
        broker = FTPBroker(request_queue, data_base_directory(), data_file_extension(), temp_directory(),
                           logging_connection, _exception_handler, delta_time, combi_sensor_ids,
                           combi_sensor_descriptions)

        try:
            # when:
            broker.feed_modified_file(a_file_path())
            got_message_id, got_station_id, got_data = request_queue.get(timeout=5.0)
            got_file_name = got_message_id  # the message id is identical to the file name

            # then:
            self.assertEqual(got_file_name, a_file_name())
            self.assertEqual(got_station_id, a_station_id())
            self.assertEqual(len(got_data), 2143)
        finally:
            broker.stop_and_join()


class TestFTPServerSideProxyProcess(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def _get_proxy_process_settings(use_db_throwing_on_add_data=False, use_db_throwing_on_register=False):
        request_queue = Queue()
        logging_queue = Queue()
        exception_queue = Queue()
        result_queue = Queue()

        database_service_factory = SQLDatabaseServiceFactoryMock(result_queue,
                                                                 use_db_throwing_on_add_data,
                                                                 use_db_throwing_on_register)
        parent = ProxyParentMock(result_queue)
        logging_connection = MultiProcessConnector(logging_queue, 0)
        dataset_time = datetime.datetime(year=2016, month=5, day=10)

        proxy = FTPServerSideProxyProcess()
        proxy_process = Process(
            target=proxy.process, args=(request_queue, database_service_factory, parent, logging_connection,
                                        partial(_exception_handler, queue=exception_queue)))

        dataset = [WeatherStationDataset(dataset_time)]
        message_id, __ = os.path.splitext(a_file_name())

        return proxy_process, request_queue, result_queue, exception_queue, message_id, dataset

    def test_process(self):
        # given:
        proxy_process, request_queue, result_queue, exception_queue, message_id, dataset = \
            self._get_proxy_process_settings()
        queue_data = (message_id, a_station_id(), dataset)

        try:
            proxy_process.start()

            # when:
            request_queue.put(queue_data)
            received_message = result_queue.get(timeout=5.0)  # type: WeatherMessage

            # then:
            self.assertEqual(received_message.get_station_id(), a_station_id())
            self.assertEqual(received_message.get_data(), dataset)
            self.assertEqual(received_message.get_message_id(), message_id)
        finally:
            request_queue.put((None, None, None))  # finish the process
            if proxy_process.is_alive():
                proxy_process.join()

    def test_process_with_handled_database_exception(self):
        # given:
        proxy_process, request_queue, result_queue, exception_queue, message_id, dataset = \
            self._get_proxy_process_settings(use_db_throwing_on_add_data=True)
        queue_data = (message_id, a_station_id(), dataset)

        try:
            proxy_process.start()

            # when:
            request_queue.put(queue_data)
            got_acknowleded_message_id = result_queue.get(timeout=5.0)

            # then:
            self.assertEqual(got_acknowleded_message_id, message_id)
        finally:
            request_queue.put((None, None, None))  # finish the process
            if proxy_process.is_alive():
                proxy_process.join()

    def test_process_exception_transfer(self):
        # given:
        proxy_process, request_queue, result_queue, exception_queue, message_id, dataset = \
            self._get_proxy_process_settings(use_db_throwing_on_register=True)
        try:
            proxy_process.start()

            # when:
            got_exception = exception_queue.get(timeout=5.0)

            # then:
            self.assertRaises(NotExistingError, got_exception.re_raise)
        finally:
            request_queue.put((None, None, None))  # finish the process even if no exception has been thrown
            if proxy_process.is_alive():
                proxy_process.join()


class TestFTPServerSideProxy(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_process(self):
        # given:
        logging_queue = Queue()
        exception_queue = Queue()
        result_queue = Queue()

        database_service_factory = SQLDatabaseServiceFactoryMock(result_queue)
        logging_connection = MultiProcessConnector(logging_queue, 0)

        config = FTPReceiverConfigSection(data_directory(), data_base_directory() + os.sep + "temp",
                                          data_file_extension(), datetime.timedelta(minutes=10))

        # when:
        with FTPServerSideProxy(
                database_service_factory,
                config,
                logging_connection,
                exception_queue):
            time.sleep(0.5)

        # then: this is a smoke test, all underlying functionality is tested in other tests

if __name__ == '__main__':
    unittest.main()
