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


class FTPServerBrokerProcess(object):
    def __init__(self):
        self._data_file_extension = ".ZIP" # TODO: possibly generalize this
        self._data_folder = "C:\\Users\\Ralf\\Documents\\test" # TODO: not yet implemented
        self._temp_data_folder = "C:\\Users\\Ralf\\Documents\\test\\temp" # TODO: not yet implemented


    def process(self, received_file_queue, request_queue):
        try:
            while (True):
                full_path = received_file_queue.get()
                message_ID, station_ID, data = self._on_new_data(full_path)
                if message_ID:
                    request_queue.put((message_ID, station_ID, data))
        except Exception as e:
            print(e) # TODO: handler still missing


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
        for curr_file_name in new_data_file_list:
            file = PCWetterstationFormatFile(self._temp_data_folder, curr_file_name) # TODO: the data from different files needs to be merged
            data = file.read()
            data = data[0]

        # delete the temporary data files
        PCWetterstationFormatFile.deletedatafiles(self._temp_data_folder, new_data_file_list)

        return data


class FTPServerBroker(object):
    """Server broker for weather data transmission based on FTP"""

    def __init__(self, request_queue):
        self._data_folder = "C:\\Users\\Ralf\\Documents\\test" # TODO: not yet implemented
        self._data_file_extension = ".ZIP" # TODO: possibly generalize this

        self._received_file_queue = Queue()
        self._filesystem_observer = FileSystemObserver(self._data_folder)
        self._filesystem_observer_process = Process(target=self._filesystem_observer.process, args=(self._received_file_queue, ))
        self._filesystem_observer_process.start()

        self._broker = FTPServerBrokerProcess()
        self._broker_process = Process(target=self._broker.process, args=(self._received_file_queue, request_queue))
        self._broker_process.start()


    def join(self):
        self._filesystem_observer.stop()
        self._filesystem_observer_process.join()
        self._broker_process.stop()
        self._broker_process.join()


    def send_persistence_acknowledgement(self, message_ID):
        print( message_ID ) # TODO: temp

        # delete the ZIP-file corresponding to the message ID
        os.remove(self._data_folder + '/' + message_ID + self._data_file_extension)


class FTPServerSideProxyProcess(object):
    def process(self, request_queue, database_service_factory, parent):
        try:
            database_service = database_service_factory.create()
            database_service.register_observer(parent)

            while (True):
                # the FTP-broker does not require deserialization of the data
                message_ID, station_ID, raw_data = request_queue.get()          
                message = WeatherMessage(message_ID, station_ID, raw_data)    
                database_service.add_data(message)
        except Exception as e:
            print(e) # TODO: handler still missing


class FTPServerSideProxy(IServerSideProxy):
    """Class for a weather server broker proxy based on FTP"""

    def __init__(self, database_service_factory):
        request_queue = Queue()      
        self._broker = FTPServerBroker(request_queue)
        self._proxy = FTPServerSideProxyProcess()
       
        self._proxy_process = Process(target=self._proxy.process, args=(request_queue, database_service_factory, self))
        self._proxy_process.start()    
        

    def join(self):
        self._broker.join()
        self._proxy_process.stop()
        self._proxy_process.join()


    def acknowledge_persistence(self, finished_ID):
        self._broker.send_persistence_acknowledgement(finished_ID)
