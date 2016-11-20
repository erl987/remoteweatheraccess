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

import sys
from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory
from weathernetwork.server.config import FTPWeatherServerIniFile
from weathernetwork.common.logging import MultiProcessLogger, IMultiProcessLogger
from multiprocessing import Queue


def main():
    """Weather server listening for data via FTP.

    Command line arguments:
    configuration INI-file
    """
    # read the configuration file (specified in the first command line argument)
    if len(sys.argv) <= 1 or len(sys.argv) > 1 and sys.argv[1].lower() == "help":
        print("Weather server listening for data via FTP. Usage: python ftp_weather_server.py config.ini")
    else:
        config_file_handler = FTPWeatherServerIniFile(sys.argv[1])
        configuration = config_file_handler.read()

        with MultiProcessLogger(True, configuration.get_log_config()) as logger:
            try:
                exception_queue = Queue()
                sql_database_service_factory = SQLDatabaseServiceFactory(
                    configuration.get_database_config().get_db_file_name(),
                    logger.get_connection()
                )

                # main server loop
                with FTPServerSideProxy(
                        sql_database_service_factory,
                        configuration.get_ftp_receiver_settings(),
                        logger.get_connection(),
                        exception_queue
                ):
                    logger.log(IMultiProcessLogger.INFO, "Server is running.")
                
                    # stall the main thread until the program is finished
                    exception_from_subprocess = None
                    try:
                        exception_from_subprocess = exception_queue.get()
                    except KeyboardInterrupt:
                        pass

                    if exception_from_subprocess:
                        exception_from_subprocess.re_raise()
            except Exception as e:
                logger.log(IMultiProcessLogger.ERROR, repr(e))

            logger.log(IMultiProcessLogger.INFO, "Server has stopped.")


if __name__ == "__main__":
    main()
