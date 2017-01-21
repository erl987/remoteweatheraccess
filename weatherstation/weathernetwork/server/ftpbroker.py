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

import datetime
import glob
import os
import signal
import threading
import time
from datetime import timedelta
from multiprocessing import Event, Process, Queue
from zipfile import ZipFile

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from weathernetwork.common.datastructures import WeatherMessage
from weathernetwork.common.exceptions import DelayedException, FileParseError
from weathernetwork.common.fileformats import PCWetterstationFormatFile
from weathernetwork.common.logging import MultiProcessLoggerProxy, IMultiProcessLogger
from weathernetwork.server.exceptions import AlreadyExistingError, NotExistingError
from weathernetwork.server.interface import IServerSideProxy


class FileSystemObserver(FileSystemEventHandler):
    """Watcher for file system changes"""
    def __init__(self, data_directory):
        """
        Constructor.

        :param data_directory:          watch directory
        :type data_directory:           str
        """
        self._data_directory = data_directory
        self._received_file_queue = None
        self._exception_event = Event()
        self._processed_files_lock = None
        self._processed_files = dict()

    def stop(self):
        """Stops watching."""
        self._exception_event.set()

    def set_received_file_queue(self, received_file_queue):
        """
        (Re-) sets the queue for transferring detected file changes.

        :param received_file_queue:     queue for that will transfer detected file changes
        :type received_file_queue:      multiprocessing.queues.Queue
        """
        self._received_file_queue = received_file_queue

    def _remove_outdated_processed_files(self, curr_time, max_keeping_time=10):
        """
        Removes too old processed message IDs from the list.

        :param curr_time:               current UTC-time
        :type curr_time:                datetime.datetime
        :param  max_keeping_time:       maximum time period to consider files to be processed
                                        (in seconds)
        :type max_keeping_time:         int
        """
        removal_list = []
        for file in self._processed_files.keys():
            if (curr_time - self._processed_files[file]) > timedelta(seconds=max_keeping_time):
                removal_list.append(file)

        for item in removal_list:
            del self._processed_files[item]

    def on_modified(self, event):
        """
        Called when a file has been modified.

        :param event:                   file change event
        :type event:                    watchdog.events.FileSystemEvent
        """
        if not event.is_directory:
            # ensure that this file has not yet been processed
            # (workaround for the watchdog library reporting possibly multiple "modified" events for a single file)
            full_path = event.src_path
            curr_time = datetime.datetime.utcnow()
            with self._processed_files_lock:
                self._remove_outdated_processed_files(curr_time)
                already_processed = full_path in self._processed_files
                self._processed_files[full_path] = curr_time

            if not already_processed:
                self._received_file_queue.put(full_path)

    def process(self, received_file_queue, exception_handler):
        """
        The file watcher process.

        :param received_file_queue:     queue transfering the detected changed files
        :type received_file_queue:      multiprocessing.queues.Queue
        :param exception_handler:       exception handler callback method receiving all exception from the process
        :type exception_handler:        method
        """
        filesystem_observer = Observer()
        try:
            # required for correct handling of Crtl + C in a multiprocess environment
            signal.signal(signal.SIGINT, signal.SIG_IGN)

            self._processed_files_lock = threading.Lock()

            self._received_file_queue = received_file_queue
            if not os.path.isdir(self._data_directory):
                raise IOError("Data directory \"%s\" not found." % self._data_directory)

            filesystem_observer.schedule(self, self._data_directory, recursive=True)
            filesystem_observer.start()

            # wait until stop is signalled
            self._exception_event.wait()
        except Exception as e:
            exception_handler(DelayedException(e))
        finally:
            if filesystem_observer.is_alive():
                filesystem_observer.stop()
                filesystem_observer.join()

    def feed_modified_file(self, full_path):
        """
        Feeds a data file manually into the queue of received files.

        :param full_path:               full path of the file to be fed into the queue of received files.
        :type full_path:                str
        """
        self._received_file_queue.put(full_path)


class FTPServerBrokerProcess(object):
    """Broker for the FTP-based weather server"""
    def __init__(self, data_directory, data_file_extension, temp_data_directory, delta_time, combi_sensor_ids,
                 combi_sensor_descriptions):
        """
        Constructor.

        :param data_directory:          watch directory
        :type data_directory:           str
        :param data_file_extension:     file extension of the data files (example: ".ZIP")
        :type data_file_extension:      str
        :param temp_data_directory:     temporary directory for unzipped the data files
        :type temp_data_directory:      str
        :param delta_time:              time period between two weather data timepoints, in minutes
        :type delta_time:               float
        :param combi_sensor_ids:        ids of the combi sensors
        :type combi_sensor_ids:         list of str
        :param combi_sensor_descriptions: descriptions of the combi sensors (with the combi sensor IDs as keys)
        :type combi_sensor_descriptions: dict(str, str)
        """
        self._data_directory = data_directory
        self._data_file_extension = data_file_extension
        self._temp_data_directory = temp_data_directory
        self._delta_time = delta_time
        self._combi_sensor_IDs = combi_sensor_ids
        self._combi_sensor_descriptions = combi_sensor_descriptions

    def process(self, received_file_queue, request_queue, parent, logging_connection, exception_handler):
        """
        The broker process.

        :param received_file_queue:     queue used for obtaining the received weather data files
        :type received_file_queue:      multiprocessing.queues.Queue
        :param request_queue:           queue used for transfering the processed file metadata further downstream
        :type request_queue:            multiprocessing.queues.Queue
        :param parent:                  parent object
        :type parent:                   FTPBroker
        :param logging_connection:      connection to the logger in the main process
        :type logging_connection:       common.logging.MultiProcessConnector
        :param exception_handler:       exception handler callback method receiving all exception from the process
        :type exception_handler:        method
        """
        try:
            # logger in the main process
            logger = MultiProcessLoggerProxy(logging_connection)

            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while True:
                full_path = received_file_queue.get()
                if full_path is None:
                    break

                message_id, station_id, data = self._on_new_data(full_path, logger, parent)
                if message_id:
                    request_queue.put((message_id, station_id, data))
        except Exception as e:
            exception_handler(DelayedException(e))

    @staticmethod
    def get_station_id(message_id):
        """
        Obtains the station ID from a message id.

        :param message_id:              message id to be split
        :type message_id:               str
        :return:                        extracted station id
        :rtype:                         str
        """
        splitted_message_id = message_id.split('_')
        station_id = splitted_message_id[-1]

        return station_id

    def _on_new_data(self, full_path, logger, parent):
        """
        Called when a new file has been received via FTP (i.e. modified)

        :param full_path:               path of the new file
        :type full_path:                str
        :param logger:                  logger
        :type logger:                   MultiProcessLoggerProxy
        :param parent:                  parent of the object
        :type parent:                   server.ftpbroker.FTPBroker
        :return:                        message id, station id, data from the new file
        :rtype:                         tuple(str, str, list of common.datastructures.WeatherStationDataset)
        """
        # extract all required information from the name of the transferred data file
        file, file_extension = os.path.splitext(full_path)
        file_path, message_id = os.path.split(file)

        if file_extension.upper() == self._data_file_extension.upper():
            station_id = FTPServerBrokerProcess.get_station_id(message_id)
            if len(station_id) > 0:
                try:
                    # ensure that the file is in its correct data subdirectory
                    if not file_path.endswith(station_id):
                        raise FileParseError(
                            "The data file \"%s\" is not in its correct subdirectory \"%s\"" % (message_id, station_id)
                        )

                    data = self._read_data_files(message_id, station_id)
                except FileParseError as e:
                    # invalid file format, ignore the file
                    logger.log(IMultiProcessLogger.WARNING, e.msg)

                    # the sender needs to acknowledge anyway, that the data does not need to be stored anymore
                    parent.send_persistence_acknowledgement(message_id, logger)
                else:
                    return message_id, station_id, data

        return None, None, None

    def _read_data_files(self, message_id, station_id):
        """
        Unzips and reads a received data file.

        :param message_id:              id of the message
        :type message_id:               str
        :param station_id:              id of the station
        :type station_id:               str
        :return:                        the read data
        :rtype:                         list of common.datastructures.WeatherStationDataset
        """
        wait_time = 0.05    # wait time between data file reading trials (in seconds)
        max_trials = 100     # reading trials for the data file before a fatal failure is assumed

        new_data_file_list = None
        try:
            # extract data from the ZIP-file(s)
            file_still_blocked = True
            counter = 0
            while file_still_blocked:
                try:
                    zip_file = ZipFile(
                        self._data_directory + os.sep + station_id + os.sep + message_id + self._data_file_extension,
                        'r'
                    )
                except PermissionError:
                    # workaround because the watchdog library cannot monitor the file close event and the file may still
                    # be open when the "modified" event is signalled
                    counter += 1
                    if counter > max_trials:
                        raise
                    time.sleep(wait_time)
                else:
                    file_still_blocked = False
                    with zip_file:
                        new_data_file_list = zip_file.namelist()
                        zip_file.extractall(self._temp_data_directory)

            # read a list of WeatherData objects from the unzipped data files
            data = list()
            for curr_file_name in new_data_file_list:
                weather_file = PCWetterstationFormatFile(self._combi_sensor_IDs, self._combi_sensor_descriptions)
                curr_data = weather_file.read(
                    self._temp_data_directory + os.sep + curr_file_name, station_id, self._delta_time
                )
                data += curr_data[0]
        finally:
            # delete the temporary data files
            if new_data_file_list:
                PCWetterstationFormatFile.delete_datafiles(self._temp_data_directory, new_data_file_list)

        return data


class FTPBroker(object):
    """Broker for the FTP-based weather server"""
    def __init__(self, request_queue, data_directory, data_file_extension, temp_data_directory, logging_connection,
                 exception_handler, delta_time, combi_sensor_ids, combi_sensor_descriptions):
        """
        Constructor.

        :param request_queue:           queue used for transfering the processed file metadata further downstream
        :type request_queue:            multiprocessing.queues.Queue
        :param data_directory:          watch directory
        :type data_directory:           str
        :param data_file_extension:     file extension of the data files (example: ".ZIP")
        :type data_file_extension:      str
        :param temp_data_directory:     temporary directory for unzipped the data files
        :type temp_data_directory:      str
        :param logging_connection:      connection to the logger in the main process
        :type logging_connection:       common.logging.MultiProcessConnector
        :param exception_handler:       exception handler callback method receiving all exception from the process
        :type exception_handler:        method
        :param delta_time:              time period between two weather data timepoints, in minutes
        :type delta_time:               float
        :param combi_sensor_ids:        ids of the combi sensors
        :type combi_sensor_ids:         list of str
        :param combi_sensor_descriptions: descriptions of the combi sensors (with the combi sensor IDs as keys)
        :type combi_sensor_descriptions: dict(str, str)
        """
        self._data_directory = data_directory
        self._data_file_extension = data_file_extension

        self._received_file_queue = Queue()
        self._filesystem_observer = FileSystemObserver(self._data_directory)
        self._filesystem_observer_process = Process(
            target=self._filesystem_observer.process, args=(self._received_file_queue, exception_handler)
        )
        self._filesystem_observer.set_received_file_queue(self._received_file_queue)
        self._filesystem_observer_process.start()

        self._broker = FTPServerBrokerProcess(
            data_directory, data_file_extension, temp_data_directory, delta_time, combi_sensor_ids,
            combi_sensor_descriptions
        )
        self._broker_process = Process(
            target=self._broker.process,
            args=(self._received_file_queue, request_queue, self, logging_connection, exception_handler)
        )
        self._broker_process.start()

    def stop_and_join(self):
        """Stops the subprocess of the object and returns afterwards."""
        self._filesystem_observer.stop()
        self._filesystem_observer_process.join()
        self._received_file_queue.put(None)
        self._broker_process.join()

    def feed_modified_file(self, full_path):
        """
        Feeds a data file manually into the queue of received files.

        :param full_path:               full path of the file to be fed into the queue of received files.
        :type full_path:                str
        """
        self._filesystem_observer.feed_modified_file(full_path)

    def send_persistence_acknowledgement(self, message_id, logger):
        """
        Sends the acknowledgement of a message being successfully stored in the SQL database to the client.
        The FTP-based data transfer relies only on an acknowledgement of the FTP-server and thus only performs local
        cleanup and logging.

        :param message_id:              id of the message
        :type message_id:               str
        :param logger:                  logger
        :type logger:                   IMultiProcessLogger
        """
        station_id = FTPServerBrokerProcess.get_station_id(message_id)

        # delete the ZIP-file corresponding to the message ID
        os.remove(self._data_directory + '/' + station_id + '/' + message_id + self._data_file_extension)

        logger.log(IMultiProcessLogger.INFO, "Successfully transferred message %s" % message_id)


class FTPServerSideProxyProcess(object):
    """Subprocess for a server side proxy for the FTP-based weather server"""
    @staticmethod
    def process(request_queue, database_service_factory, parent, logging_connection, exception_handler):
        """
        The process of the server side proxy.

        :param request_queue:           queue used for transfering the processed file metadata further downstream
        :type request_queue:            multiprocessing.queues.Queue
        :param database_service_factory:factory creating SQL database services
        :type database_service_factory: server.sqldatabase.SQLDatabaseServiceFactory
        :param parent:                  parent object
        :type parent:                   FTPServerSideProxy
        :param logging_connection:      connection to the logger in the main process
        :type logging_connection:       common.logging.MultiProcessConnector
        :param exception_handler:       exception handler callback method receiving all exception from the process
        :type exception_handler:        method
        """
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            database_service = database_service_factory.create(True)
            database_service.register_observer(parent)
            logger = MultiProcessLoggerProxy(logging_connection)

            while True:
                # the FTP-broker does not require deserialization of the data
                message_id, station_id, raw_data = request_queue.get()
                if message_id is None:
                    break
                message = WeatherMessage(message_id, station_id, raw_data)
                try:
                    database_service.add_data(message)
                except (NotExistingError, AlreadyExistingError) as e:
                    # the new data will be ignored
                    logger.log(IMultiProcessLogger.WARNING, e.msg)

                    # the sender needs to acknowledge anyway, that the data does not need to be stored anymore
                    parent.acknowledge_persistence(message_id, logger)

                if not raw_data:
                    logger.log(IMultiProcessLogger.WARNING, "Data for station %s was empty." % station_id)
        except Exception as e:
            exception_handler(DelayedException(e))


class FTPServerSideProxy(IServerSideProxy):
    """
    Server side proxy for the FTP-based weather server.
    Needs to be called in a with-clause for correct management of the subprocesses.
    """
    def __init__(self, database_service_factory, config, logging_connection, exception_queue):
        """
        Constructor.

        :param database_service_factory:factory creating SQL database services
        :type database_service_factory: server.sqldatabase.IDatabaseServiceFactory
        :param config:                  configuration of the FTP-based weather server
        :type config:                   server.config.FTPReceiverConfigSection
        :param logging_connection:      connection to the logger in the main process
        :type logging_connection:       common.logging.MultiProcessConnector
        :param exception_queue:         queue for transporting exceptions to the main process
        :type exception_queue:          multiprocessing.queues.Queue
        """
        # read the configuration
        data_directory, temp_data_directory, data_file_extension, delta_time = config.get()

        # obtain the combi sensors existing in the database
        database_service = database_service_factory.create(False)  # no logging, because called from the main process
        combi_sensor_ids, combi_sensor_descriptions = database_service.get_combi_sensors()

        # empty the temporary data directory (it may contain unnecessary files after a power failure)
        self._clear_temp_data_directory(temp_data_directory)

        # find all still unstored data files
        unstored_file_paths = self._find_all_data_files(data_directory, data_file_extension)

        # start the listener processes
        self._exception_queue = exception_queue
        self._request_queue = Queue()
        self._broker = FTPBroker(
            self._request_queue,
            data_directory,
            data_file_extension,
            temp_data_directory,
            logging_connection,
            self._exception_handler,
            delta_time,
            combi_sensor_ids,
            combi_sensor_descriptions
        )
        self._proxy = FTPServerSideProxyProcess()
        self._proxy_process = Process(
            target=self._proxy.process,
            args=(self._request_queue, database_service_factory, self, logging_connection, self._exception_handler)
        )
        self._proxy_process.start()

        # feed the still unstored data files into the listener process
        self._feed_unstored_data_files(unstored_file_paths)

    def __enter__(self):
        """
        Enter method for context managers.

        :return:                    the class instance
        :rtype:                     FTPServerSideProxy
        """
        return self

    def __exit__(self, type_val, value, traceback):
        """
        Exit method for context managers.

        :param type_val:            exception type
        :param value:               exception value
        :param traceback:           exception traceback
        """
        self._stop_and_join()

    @staticmethod
    def _clear_temp_data_directory(temp_data_directory):
        """
        Clears the temporary data directory.

        :param temp_data_directory: temporary data directory
        :type temp_data_directory:  str
        """
        files = glob.glob(temp_data_directory + '/*')
        for f in files:
            os.remove(f)

    @staticmethod
    def _find_all_data_files(data_directory, data_file_extension):
        """
        Finds all data files in the data directory and all subdirectories.
        All files in the data directory are assumed to be unsaved in the SQL database.

        :param data_directory:          data directory
        :type data_directory:           str
        :param data_file_extension:     file extension of the data files (example: ".ZIP")
        :type data_file_extension:      str
        :return:                        all unstored files
        :rtype:                         list of str
        """
        # recursive search in subdirectories
        unstored_file_paths = []
        for root, dirnames, filenames in os.walk(data_directory):
            unstored_file_paths += glob.glob(root + "/*" + data_file_extension)

        return unstored_file_paths

    def _feed_unstored_data_files(self, unstored_file_paths):
        """
        Feeds all unstored files into the queue of received files.

        :param unstored_file_paths:     list of the unstored weather data files
        :type unstored_file_paths:      list of str
        """
        for file_path in unstored_file_paths:
            self._broker.feed_modified_file(file_path)

    def _stop_and_join(self):
        """Stops the subprocess of the instance and returns afterwards"""
        self._broker.stop_and_join()
        self._request_queue.put((None, None, None))
        self._proxy_process.join()

    def acknowledge_persistence(self, finished_id, logger):
        """
        Performs the acknowledgement of a successful finished message transfer to the client

        :param finished_id:     id of the finished message
        :type finished_id:      str
        :param logger:          logging system of the server
        :type logger:           common.logging.IMultiProcessLogger
        """
        self._broker.send_persistence_acknowledgement(finished_id, logger)

    def _exception_handler(self, exception):
        """
        Exception handler passing any exception to the main process.

        :param exception:       exception risen by a subprocess
        :type exception:        DelayedException
        """
        self._exception_queue.put(exception)
