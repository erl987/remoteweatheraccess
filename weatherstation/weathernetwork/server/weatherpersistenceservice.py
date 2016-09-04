from multiprocessing import Queue, Process, Event
from weathernetwork.server.iweatherpersistenceservice import IWeatherPersistenceService
from weathernetwork.server.storageprocess import StorageProcess
from weathernetwork.common.delayedexception import DelayedException

class WeatherPersistenceService(IWeatherPersistenceService):
    """Service storing weather data in a database"""

    def __init__(self, server_proxy, storage_object, db_file_name):
        self._server_proxy = server_proxy
        self._server_proxy.register_listener(self)
        
        self._storage_queue = Queue()
        self._acknowledgement_queue = Queue()
        self._exception_event = Event()
        self._exception_queue = Queue()

        self._storage_process = Process(target=storage_object.storage_worker, args=(db_file_name, self._storage_queue, self._acknowledgement_queue, self._exception_handler))
        self._acknowledgement_process = Process(target=self._acknowledgement_worker_process, args=(self._acknowledgement_queue, server_proxy, self._exception_handler))
        

    def __enter__(self):
        self._acknowledgement_process.start()  
        self._storage_process.start()         
        return self
    

    def __exit__(self, type, value, traceback):
        self._server_proxy.join()
        self._storage_queue.put(None)
        self._storage_process.join()
        self._acknowledgement_queue.put(None)
        self._acknowledgement_process.join()     


    def add_data(self, message):
        self._storage_queue.put(message)


    def wait_for_next_data(self):
        self._server_proxy.wait_for_next_data()


    def _acknowledgement_worker_process(self, acknowledgement_queue, server_proxy, exception_handler):
        """Worker process for listening for new finished dataset storages that need to be acknowledged to the client.
        """
        try:
            while (True):
                finished_storage_ID = acknowledgement_queue.get()
                if finished_storage_ID == None:
                    break
            
                server_proxy.acknowledge_persistence(finished_storage_ID)
        except Exception as e:
            exception_handler( DelayedException(e) )


    def _exception_handler(self, exception):
        self._exception_queue.put(exception)
        self._exception_event.set()


    def check_for_exceptions_in_processes(self):
        if self._exception_event.is_set():
            exception = self._exception_queue.get()
            exception.re_raise()
