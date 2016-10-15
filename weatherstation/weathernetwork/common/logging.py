import logging
import sys
import threading
from datetime import datetime
from multiprocessing import Queue
from logging.handlers import SysLogHandler
from abc import ABCMeta, abstractmethod

class IMultiProcessLogger(metaclass=ABCMeta):
    """Interface class for a multiprocessing capable logger."""

    # log levels (identical to the standard Python log levels)
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    @abstractmethod
    def log(self, log_level, message):
        pass


class MultiProcessLogger(IMultiProcessLogger):
    """Multiprocessing capable logging class. Use this class only within a context manager."""
    def __init__(self, is_print_to_screen, log_file_name=None):
        """
        Constructor.
        :param is_print_to_screen:          flag stating if the log message is additionally printed to the screen
        :type is_print_to_screen:           boolean
        :param log_file_name:               Name and path of the log file to be used. If omitted, the default log system of the platform is used.
        :type log_file_name:                string
        :raise FileNotFoundError:           if no log file name is given and the operating system has no default log system
        """
        self._is_print_to_screen = is_print_to_screen
        self._log_file_name = log_file_name
        self._logging_queue = []
        self._thread = []
        self._lock = threading.Lock()

        # initialize the logger for the present process
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        if self._log_file_name:
            logging.basicConfig(filename=log_file_name, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S')
        else:
            if sys.platform.startswith('linux'):
                syslog = SysLogHandler(address='/dev/log')
                formatter = logging.Formatter('%(name)s - %(app_name)s - %(levelname)s : %(message)s')
                syslog.setFormatter(formatter)
                logger.addHandler(syslog)
                logger = logging.LoggerAdapter(self._logger, { 'app_name': script_name } )
            else:
                # on Windows
                raise FileNotFoundError("No log file name given and the operating system has no default log system.")


    def __enter__(self):
        """
        Context manager initializer method.
        """
        with self._lock:
            self._logging_queue = Queue()
            self._thread = threading.Thread(target=self._logger_thread)
            self._thread.start()

        return self
    

    def __exit__(self, type, value, traceback):
        """
        Context manager exit method.
        """
        self.join()


    def get_connection_queue(self):
        """
        Returns the queue that can be used to feed log messages from proxies in other processes to the logger process.
        :return:                            queue connecting a MultiProcessLoggerProxy in another process to the current logger
        :rtype:                             multiprocessing.Queue
        """
        with self._lock:
            logging_queue = self._logging_queue

        return logging_queue
     

    def join(self):
        """
        Stops the underlying thread of the class. Returns only after finishing the thread.
        """
        with self._lock:
            if self._logging_queue:
                self._logging_queue.put(None)
            if self._thread:
                self._thread.join()
       
             
    def _logger_thread(self):
        """
        Logger thread waiting for incoming log messages.
        """
        while True:
            record = self._logging_queue.get()

            # check the finishing condition
            if record is None:
                break

            logger = logging.getLogger(record.name)
            logger.handle(record)
            if self._is_print_to_screen:
                self._print_to_screen(record.asctime, record.getMessage())


    def log(self, log_level, message):
        """
        Logging a message.
        :param log_level:           log level
        :type log_level:            Python log levels
        :param message:             log message
        :type message:              string
        """
        # direct logging within the same process
        logger = logging.getLogger() # this is always the root logger
        logger.log(log_level, message)

        if self._is_print_to_screen:
            curr_time = datetime.now()
            self._print_to_screen(curr_time.strftime("%b %d %H:%M:%S"), message)


    def _print_to_screen(self, timestamp, message):
        """
        Prints a log message to the screen.
        :param timestamp:           timestamp of the message
        :type timestamp:            human-readable string
        :param message:             message
        :type message:              string
        """
        print(timestamp + ": " + message)


class MultiprocessLoggerProxy(IMultiProcessLogger):
    """Proxy class for multiprocessing capable logging within another process."""

    def __init__(self, logging_queue):
        """
        Constructor.
        :param logging_queue:       Queue connecting the proxy to the logger within the logging process
        :type logging_queue:        multiprocessing.Queue object
        """
        # create a connection to the remote logger within the logging process
        log_queue_handler = logging.handlers.QueueHandler(logging_queue)
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(log_queue_handler)


    def log(self, log_level, message):
        """
        Logging a message.
        :param log_level:           log level
        :type log_level:            Python log levels
        :param message:             log message
        :type message:              string
        """
        # logging on the remote logger in another process
        self._logger.log(log_level, message)