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
import argparse
import signal
import sys
from multiprocessing import Queue

from remote_weather_access.common.logging import MultiProcessLogger, IMultiProcessLogger
from remote_weather_access.server.config import FTPWeatherServerIniFile
from remote_weather_access.server.ftpbroker import FTPServerSideProxy
from remote_weather_access.server.sqldatabase import SQLDatabaseServiceFactory
from remote_weather_access import __version__, package_name


_exception_queue = Queue()
_REGULAR_STOP = "REGULAR_STOP"


def handler_stop_signals(signum, frame):
    """
    Handles termination events, not used under Windows.

    :param signum:  signal number
    :param frame:   current stack frame
    """
    _exception_queue.put(_REGULAR_STOP)


def run_on_linux():
    """
    Stalls the main thread until the program is finished.

    :return:        exception thrown by a subprocess or _REGULAR_STOP
    """
    signal.signal(signal.SIGINT, handler_stop_signals)
    signal.signal(signal.SIGTERM, handler_stop_signals)

    # wait a regular stop or an exception
    exception_from_subprocess = _exception_queue.get()

    return exception_from_subprocess


def run_on_windows():
    """
    Stalls the main thread until the program is finished.

    :return:        exception thrown by a subprocess or None
    """
    exception_from_subprocess = None

    # wait for Crtl + C
    try:
        exception_from_subprocess = _exception_queue.get()
    except KeyboardInterrupt:
        pass

    return exception_from_subprocess


def main():
    """
    Weather server listening for data via FTP.

    Command line argument:
    configuration INI-file

    Usage:
    python ftp_weather_server.py config.ini
    """
    parser = argparse.ArgumentParser(description="Weather server listening for data via FTP.")
    parser.add_argument("ini_file", metavar="INI-FILE", type=str, help="configuration file")
    parser.add_argument("--demon", "-d", dest="demon_mode", action="store_true", help="run in demon mode")
    parser.add_argument("--version", "-v", action="version", version="{} version {}".format(package_name, __version__),
                        help='show the version information of the program')

    try:
        args = parser.parse_args()
        config_file_handler = FTPWeatherServerIniFile(args.ini_file)
        configuration = config_file_handler.read()
        do_print_logs = not args.demon_mode

        with MultiProcessLogger(is_print_to_screen=do_print_logs, log_config=configuration.get_log_config()) as logger:
            try:
                sql_database_service_factory = SQLDatabaseServiceFactory(
                    configuration.get_database_config().get_db_file_name(),
                    logger.get_connection()
                )

                # main server loop
                with FTPServerSideProxy(
                        sql_database_service_factory,
                        configuration.get_ftp_receiver_settings(),
                        logger.get_connection(),
                        _exception_queue
                ):
                    logger.log(IMultiProcessLogger.INFO, "Server is running (version {}).".format(__version__))

                    # stall the main thread until the program is finished
                    if sys.platform.startswith("win32"):
                        exception_from_subprocess = run_on_windows()
                    else:
                        exception_from_subprocess = run_on_linux()

                    if exception_from_subprocess and exception_from_subprocess != _REGULAR_STOP:
                        exception_from_subprocess.re_raise()
            except Exception as e:
                logger.log(IMultiProcessLogger.ERROR, str(e))

            logger.log(IMultiProcessLogger.INFO, "Server has stopped.")
    except Exception as e:
        print("An exception occurred: {}".format(str(e)))


if __name__ == "__main__":
    main()
