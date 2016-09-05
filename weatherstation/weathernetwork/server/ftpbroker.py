from weathernetwork.server.interface import IServerSideProxy
from weathernetwork.common.fileformats import PCWetterstationFormatFile
from weathernetwork.server.weathermessage import WeatherMessage
from weathernetwork.common.delayedexception import DelayedException
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from zipfile import ZipFile
import time
import datetime
from datetime import timedelta
import threading
from multiprocessing import Event, Process, Queue
import signal

class FileSystemObserver(FileSystemEventHandler):
    def __init__(self, data_directory):
        self._data_directory = data_directory
        self._received_file_queue = []
        self._exception_event = Event()
        self._processed_files_lock = []
        self._processed_files = dict()


    def stop(self):
        self._exception_event.set()


    def _remove_outdated_processed_files(self, curr_time, max_keeping_time = 10):
        """Removes too old processed message IDs from the list."""
        removal_list = []
        for file in self._processed_files.keys():
            if (curr_time - self._processed_files[file]) > timedelta(seconds = max_keeping_time):
                removal_list.append(file)

        for item in removal_list:
            del self._processed_files[item]


    def on_modified(self, event):
        """A file has been modified"""
        if not event.is_directory:
            # ensure that this file has not yet been processed (workaround for the watchdog library reporting possibly multiple "modified" events for a single file)
            full_path = event.src_path              
            curr_time = datetime.datetime.utcnow()   
            with self._processed_files_lock:
                self._remove_outdated_processed_files(curr_time)                
                already_processed = full_path in self._processed_files
                self._processed_files[full_path] = curr_time

            if not already_processed:
                self._received_file_queue.put(full_path)


    def process(self, received_file_queue, exception_handler):
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN) # required for correct handling of Crtl+C in a multiprocess environment
            self._processed_files_lock = threading.Lock()
            filesystem_observer = Observer()
            self._received_file_queue = received_file_queue
        
            filesystem_observer.schedule(self, self._data_directory, recursive=False)
            filesystem_observer.start()
        
            # wait until stop is signalled
            self._exception_event.wait()

            filesystem_observer.stop()
            filesystem_observer.join()
        except Exception as e:
            exception_handler(DelayedException(e))


class FTPServerBrokerProcess(object):
    def __init__(self, data_directory, data_file_extension, temp_data_directory):
        self._data_directory = data_directory        
        self._data_file_extension = data_file_extension
        self._temp_data_directory = temp_data_directory


    def process(self, received_file_queue, request_queue, exception_handler):
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while (True):
                full_path = received_file_queue.get()
                if full_path is None:
                    break;
                message_ID, station_ID, data = self._on_new_data(full_path)
                if message_ID:
                    request_queue.put((message_ID, station_ID, data))
        except Exception as e:
            exception_handler(DelayedException(e))


    def _on_new_data(self, full_path):
        """A new file has been received via FTP (i.e. modified)"""
        # extract all required information from the name of the transferred data file
        file, file_extension = os.path.splitext(full_path)
        file_path, message_ID = os.path.split(file)

        if file_extension.upper() == self._data_file_extension:
            splitted_message_ID = message_ID.split( '_' )
            if len(splitted_message_ID) > 0:
                station_ID = splitted_message_ID[-1]
                data = self._read_data_files(message_ID, station_ID)
                return message_ID, station_ID, data

        return None, None, None


    def _read_data_files(self, message_ID, station_ID):
        wait_time = 0.05    # wait time between data file reading trials (in seconds)
        max_trials = 10     # reading trials for the data file before a fatal failure is assumed

        # extract data from the ZIP-file(s)
        new_data_file_list = []
        file_still_blocked = True
        counter = 0
        while file_still_blocked:
            try:
                zip_file = ZipFile(self._data_directory + '/' + message_ID + self._data_file_extension, 'r')
            except PermissionError:
                # workaround because the watchdog library cannot monitor the file close event and the file may still be open when the "modified" event is signalled
                counter += 1
                if counter > max_trials:
                    reraise
                time.sleep(wait_time)
            else:
                file_still_blocked = False
                with zip_file:
                    new_data_file_list = zip_file.namelist()
                    zip_file.extractall(self._temp_data_directory)

        # read a list of WeatherData objects from the unzipped data files  
        for curr_file_name in new_data_file_list:
            file = PCWetterstationFormatFile(self._temp_data_directory, curr_file_name) # TODO: the data from different files needs to be merged
            data = file.read()
            data = data[0]

        # delete the temporary data files
        PCWetterstationFormatFile.deletedatafiles(self._temp_data_directory, new_data_file_list)

        return data


class FTPBroker(object):
    """Broker for weather data transmission based on FTP"""

    def __init__(self, request_queue, data_directory, data_file_extension, temp_data_directory, exception_handler):
        self._data_directory = data_directory
        self._data_file_extension = data_file_extension

        self._received_file_queue = Queue()
        self._filesystem_observer = FileSystemObserver(self._data_directory)
        self._filesystem_observer_process = Process(target=self._filesystem_observer.process, args=(self._received_file_queue, exception_handler))
        self._filesystem_observer_process.start()

        self._broker = FTPServerBrokerProcess(data_directory, data_file_extension, temp_data_directory)
        self._broker_process = Process(target=self._broker.process, args=(self._received_file_queue, request_queue, exception_handler))
        self._broker_process.start()


    def stop_and_join(self):
        self._filesystem_observer.stop()
        self._filesystem_observer_process.join()
        self._received_file_queue.put(None)
        self._broker_process.join()


    def send_persistence_acknowledgement(self, message_ID):
        print( message_ID ) # TODO: temp

        # delete the ZIP-file corresponding to the message ID
        os.remove(self._data_directory + '/' + message_ID + self._data_file_extension)


class FTPServerSideProxyProcess(object):
    def process(self, request_queue, database_service_factory, parent, exception_handler):
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            database_service = database_service_factory.create()
            database_service.register_observer(parent)

            while (True):
                # the FTP-broker does not require deserialization of the data
                message_ID, station_ID, raw_data = request_queue.get() 
                if message_ID is None:
                    break        
                message = WeatherMessage(message_ID, station_ID, raw_data)    
                database_service.add_data(message)
        except Exception as e:
            exception_handler(DelayedException(e))


class FTPServerSideProxy(IServerSideProxy):
    """
    Class for a weather server broker proxy based on FTP.
    Needs to be called in a with-clause for correct management of the subprocesses.
    """

    def __init__(self, database_service_factory, data_directory, data_file_extension, temp_data_directory, exception_queue):
        self._exception_queue = exception_queue
        self._request_queue = Queue()  
        self._broker = FTPBroker(self._request_queue, data_directory, data_file_extension, temp_data_directory, self._exception_handler)                
        self._proxy = FTPServerSideProxyProcess() 
        self._proxy_process = Process(target=self._proxy.process, args=(self._request_queue, database_service_factory, self, self._exception_handler))
        self._proxy_process.start()             

        
    def __enter__(self):
        return self
    

    def __exit__(self, type, value, traceback):
        self._stop_and_join()


    def _stop_and_join(self):
        self._broker.stop_and_join()
        self._request_queue.put((None,None,None))
        self._proxy_process.join()
        

    def acknowledge_persistence(self, finished_ID):
        self._broker.send_persistence_acknowledgement(finished_ID)


    def _exception_handler(self, exception):
        self._exception_queue.put(exception)
