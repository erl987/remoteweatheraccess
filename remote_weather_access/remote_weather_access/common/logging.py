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

import logging
import os
import sys
import threading
from datetime import datetime
from multiprocessing import Queue
from logging.handlers import SysLogHandler, RotatingFileHandler
from abc import ABCMeta, abstractmethod

from remote_weather_access.common.exceptions import RunInNotAllowedProcessError


def _remove_all_log_handlers():
    """Removes all log handlers from the root logger"""
    handlers = logging.getLogger().handlers[:]
    for handler in handlers:
        handler.close()
        logging.getLogger().removeHandler(handler)


class MultiProcessConnector(object):
    """Class representing a connector to the main logger process from other subprocesses"""
    def __init__(self, logging_queue, main_logger_pid):
        """
        Constructor.

        :param logging_queue:               queue for sending log messages to the main logger process
        :type logging_queue:                multiprocessing.Queue
        :param main_logger_pid:             process ID of the main logger process
        :type main_logger_pid:              integer
        """
        self._logging_queue = logging_queue
        self._main_logger_pid = main_logger_pid

    def get_connection_queue(self):
        """
        Obtains the queue for sending log messages to the main logger process.

        :return:                            queue for sending log messages
        :rtype:                             multiprocessing.Queue
        """
        return self._logging_queue

    def get_main_logger_pid(self):
        """
        Obtains the process ID of the main logger process.

        :return:                            process ID of the main logger process
        :rtype:                             integer
        """
        return self._main_logger_pid


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
        :param log_config:                  configuration of the log. If omitted, the default log system of the
                                            platform is used.
        :type log_config:                   server.config.LogConfigSection
        :raise FileNotFoundError:           if no log file is configured and the operating system has no default
                                            log system
        """
        self._is_print_to_screen = is_print_to_screen
        self._logging_queue = None
        self._thread = None
        self._main_logger_pid = os.getpid()
        self._lock = threading.Lock()
        self._is_joined = False

        # initialize the logger for the present process
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if log_config:
            log_file_name = log_config.get_log_file_name()
            max_bytes = log_config.get_max_kbytes_per_files() * 1024
            backup_count = log_config.get_num_files_to_keep()

            log_handler = RotatingFileHandler(log_file_name, maxBytes=max_bytes, backupCount=backup_count)
            log_handler.setFormatter(
                logging.Formatter(fmt='%(asctime)s %(levelname)s: %(message)s', datefmt='%b %d %H:%M:%S')
            )
            logger.addHandler(log_handler)
        else:
            if sys.platform.startswith('linux'):
                syslog = SysLogHandler(address='/dev/log')
                formatter = logging.Formatter('%(name)s - FTPWeatherServer - %(levelname)s : %(message)s')
                syslog.setFormatter(formatter)
                logger.addHandler(syslog)
            else:
                # on Windows
                raise FileNotFoundError("The OS has no default log system. You need to specify a log file.")

    def __enter__(self):
        """Context manager initializer method."""
        with self._lock:
            self._logging_queue = Queue()
            self._thread = threading.Thread(target=self._logger_thread)
            self._thread.start()

        return self

    def __exit__(self, type_val, value, traceback):
        """Context manager exit method."""
        self._join()

    def get_connection(self):
        """
        Returns the connection that can be used to feed messages from proxies in other processes to the logger process.

        :return:                            queue connecting a MultiProcessLoggerProxy in another process to the current
                                            logger
        :rtype:                             MultiProcessConnector
        """
        with self._lock:
            connection = MultiProcessConnector(self._logging_queue, self._main_logger_pid)

        return connection

    def _join(self):
        """Stops the underlying thread of the class. Returns only after finishing the thread."""
        with self._lock:
            if not self._is_joined:
                self._is_joined = True
                if self._logging_queue:
                    self._logging_queue.put(None)
                if self._thread:
                    self._thread.join()

                _remove_all_log_handlers()

    def _logger_thread(self):
        """Logger thread waiting for incoming log messages."""
        while True:
            record = self._logging_queue.get()

            # check the finishing condition
            if record is None:
                break

            logger = logging.getLogger(record.name)
            logger.handle(record)
            if self._is_print_to_screen:
                self._print_to_screen(record.asctime, record.levelname, record.getMessage())

    def log(self, log_level, message):
        """
        Logging a message.

        :param log_level:           log level
        :type log_level:            Python log levels
        :param message:             log message
        :type message:              string
        """
        # direct logging within the same process
        logger = logging.getLogger()  # this is always the root logger
        logger.log(log_level, message)

        if self._is_print_to_screen:
            curr_time = datetime.now()
            log_level_name = ""
            if log_level == logging.INFO:
                log_level_name = "INFO"
            elif log_level == logging.WARN:
                log_level_name = "WARNING"
            elif log_level == logging.ERROR:
                log_level_name = "ERROR"
            self._print_to_screen(curr_time.strftime("%b %d %H:%M:%S"), log_level_name, message)

    @staticmethod
    def _print_to_screen(timestamp, log_level_name, message):
        """
        Prints a log message to the screen.

        :param timestamp:           timestamp of the message
        :type timestamp:            human-readable string
        :param log_level_name:      describing the log level
        :type log_level_name:       str
        :param message:             message
        :type message:              str
        """
        print(timestamp + " " + log_level_name + ": " + message)


class MultiProcessLoggerProxy(IMultiProcessLogger):
    """Mono-state proxy class (one instance per process) for multiprocessing capable logging within another process"""
    __shared_state = {}

    def __init__(self, logging_connection):
        """Constructor. An existing logging queue for that process will be replaced by the new queue.

        :param logging_connection:  queue connecting the proxy to the logger within the logging process
        :type logging_connection:   MultiProcessConnector
        """
        # this proxy must not be used from the main logger process
        if os.getpid() == logging_connection.get_main_logger_pid():
            raise RunInNotAllowedProcessError("The logger proxy must not be run within the main logger process.")

        # this is a mono-state class (borg pattern)
        self.__dict__ = self.__shared_state

        self._logger = logging.getLogger()

        # remove all handlers already registered (there should be only one)
        _remove_all_log_handlers()

        # create a connection to the remote logger within the logging process
        log_queue_handler = logging.handlers.QueueHandler(logging_connection.get_connection_queue())
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
