import logging
import sys
import threading
from datetime import datetime
from multiprocessing import Queue
from logging.handlers import SysLogHandler, RotatingFileHandler
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
    def __init__(self, is_print_to_screen, log_config=None):
        """
        Constructor.
        :param is_print_to_screen:          flag stating if the log message is additionally printed to the screen
        :type is_print_to_screen:           boolean
        :param log_config:                  Configuration of the log. If omitted, the default log system of the platform is used.
        :type log_config:                   LogConfig object
        :raise FileNotFoundError:           if no log file is configured and the operating system has no default log system
        """
        self._is_print_to_screen = is_print_to_screen
        self._logging_queue = []
        self._thread = []
        self._lock = threading.Lock()

        # initialize the logger for the present process
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        if log_config:
            log_file_name = log_config.get_log_file_name()
            max_bytes = log_config.get_max_kbytes_per_files() * 1024
            backup_count = log_config.get_num_files_to_keep()

            log_handler = RotatingFileHandler(log_file_name, maxBytes=max_bytes, backupCount=backup_count)
            log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
            logger.addHandler(log_handler)
        else:
            if sys.platform.startswith('linux'):
                syslog = SysLogHandler(address='/dev/log')
                formatter = logging.Formatter('%(name)s - %(app_name)s - %(levelname)s : %(message)s')
                syslog.setFormatter(formatter)
                logger.addHandler(syslog)
                logger = logging.LoggerAdapter(self._logger, { 'app_name': script_name })  # TODO: most probably this is wrong
            else:
                # on Windows
                raise FileNotFoundError("The OS has no default log system. You need to specify a log file.")


    def __enter__(self):
        """
        Context manager initializer method.
        """
        with self._lock:
            self._logging_queue = Queue()
            self._thread = threading.Thread(target=self._logger_thread)
            self._thread.start()

        return self
    

    def __exit__(self, type_val, value, traceback):
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

    @staticmethod
    def _print_to_screen(timestamp, message):
        """
        Prints a log message to the screen.
        :param timestamp:           timestamp of the message
        :type timestamp:            human-readable string
        :param message:             message
        :type message:              string
        """
        print(timestamp + ": " + message)


class MultiprocessLoggerProxy(IMultiProcessLogger):
    """Proxy class for multiprocessing capable logging within another process. DO NOT USE IT FROM THE SAME PROCESS."""

    def __init__(self, logging_queue):
        """Constructor.
        WARNING: THIS QUEUE WILL ONLY BE REGISTERED IF NONE WAS REGISTERED FOR THAT PROCESS BEFORE!

        :param logging_queue:       Queue connecting the proxy to the logger within the logging process
        :type logging_queue:        multiprocessing.Queue object
        """
        # create a connection to the remote logger within the logging process
        self._logger = logging.getLogger()

        # do not register the logging queue if another queue has already been registered for the current process
        if not self._logger.hasHandlers():
            log_queue_handler = logging.handlers.QueueHandler(logging_queue)
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