from watchdog.observers import Observer
from weathernetwork.server.iserversideproxy import IServerSideProxy
from weathernetwork.common.fileformats import PCWetterstationFormatFile
from weathernetwork.server.weathermessage import WeatherMessage
from weathernetwork.common.delayedexception import DelayedException
from watchdog.events import FileSystemEventHandler
import os
from zipfile import ZipFile
import time
import datetime
from datetime import timedelta
import threading
from multiprocessing import Event, Process, Queue

class FileSystemObserver(FileSystemEventHandler):
    def __init__(self, data_folder):
        self._data_folder = data_folder
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


    def process(self, received_file_queue): # TODO: any exception MUST be transferred to the main process
        self._processed_files_lock = threading.Lock()
        filesystem_observer = Observer()
        self._received_file_queue = received_file_queue
        
        filesystem_observer.schedule(self, self._data_folder, recursive=False)
        filesystem_observer.start()
        
        # wait until stop is signalled
        self._exception_event.wait()

        filesystem_observer.stop()
        filesystem_observer.join()


class FTPServerBroker(object):
    """Server broker for weather data transmission based on FTP"""

    def __init__(self):
        self._proxies = []
        self._data_file_extension = ".ZIP" # TODO: possibly generalize this
        self._data_folder = "C:\\Users\\Ralf\\Documents\\test" # TODO: not yet implemented

        self._received_file_queue = Queue()
        self._filesystem_observer = FileSystemObserver(self._data_folder)
        self._filesystem_observer_process = Process(target=self._filesystem_observer.process, args=(self._received_file_queue, ))
        self._filesystem_observer_process.start()


    def register_proxy(self, proxy):
        """Registers a new proxy for that broker.
        :param proxy:    new proxy to be registered
        :type proxy:     IServerSideProxy
        """
        self._proxies.append(proxy)


    def remove_listener(self, proxy):
        self._proxies.remove(proxy)


    def join(self):
        self._filesystem_observer.stop()
        self._filesystem_observer_process.join()


    def wait_for_next_data(self):
        """Waiting for the next message to arrive."""
        full_path = self._received_file_queue.get()
        self._on_new_data(full_path)


    def send_persistence_acknowledgement(self, message_ID):
        print( message_ID ) # TODO: temp

        # delete the ZIP-file corresponding to the message ID
        os.remove(self._data_folder + '/' + message_ID + self._data_file_extension)


    def _on_new_data(self, full_path):
        """A new file has been received via FTP (i.e. modified)"""
        # extract all required information from the name of the transferred data file
        file, file_extension = os.path.splitext(full_path)
        file_path, message_ID = os.path.split(file)

        if file_extension.upper() == self._data_file_extension:
            splitted_message_ID = message_ID.split( '_' )
            if len(splitted_message_ID) > 0:
                station_ID = splitted_message_ID[-1]

                self._notify_proxies(message_ID, station_ID)


    def _notify_proxies(self, message_ID, station_ID):
        for proxy in self._proxies:
            proxy.on_data_received(message_ID, station_ID)


class FTPServerSideProxy(IServerSideProxy):
    """Class for a weather server broker proxy based on FTP"""

    def __init__(self):
        self._observers = []
        self._broker = FTPServerBroker()
        self._broker.register_proxy(self)        
        self._data_file_extension = ".ZIP" # TODO: possibly generalize this
        self._data_folder = "C:\\Users\\Ralf\\Documents\\test" # TODO: not yet implemented
        self._temp_data_folder = "C:\\Users\\Ralf\\Documents\\test\\temp" # TODO: not yet implemented

    def register_listener(self, observer):
        """ Registers a new listener.
        :param observer:    new listener to be registered
        :type observer:     IWeatherPersistenceService
        """
        self._observers.append(observer)


    def remove_listener(self, observer):
        self._observers.remove(observer)


    def join(self):
        self._broker.join()


    def acknowledge_persistence(self, finished_ID):
        self._broker.send_persistence_acknowledgement(finished_ID)


    def wait_for_next_data(self):
        self._broker.wait_for_next_data()


    def on_data_received(self, message_ID, station_ID):
        wait_time = 0.05 # wait time between data file reading trials (in seconds)
        max_trials = 10 # reading trials for the data file before a fatal failure is assumed

        # extract data from the ZIP-file(s)
        new_data_file_list = []
        file_still_blocked = True
        counter = 0
        while file_still_blocked:
            try:
                zip_file = ZipFile(self._data_folder + '/' + message_ID + self._data_file_extension, 'r')
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
                    zip_file.extractall(self._temp_data_folder)

        # read a list of WeatherData objects from the unzipped data files
        datasets = []
        try:
            for curr_file_name in new_data_file_list:
                file = PCWetterstationFormatFile(self._temp_data_folder, curr_file_name)
                data = file.read()
                data = data[0]
        except Exception as e:
                raise(e)

        message = WeatherMessage(message_ID, station_ID, data)
        self._notify_listeners(message)

        # delete the temporary data files
        PCWetterstationFormatFile.deletedatafiles(self._temp_data_folder, new_data_file_list)


    def _notify_listeners(self, message):
        for observer in self._observers:
            observer.add_data(message)
