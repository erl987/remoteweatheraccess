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

from weathernetwork.server.ftpbroker import FTPServerSideProxy
from weathernetwork.server.sqldatabase import SQLDatabaseServiceFactory
from weathernetwork.common.logging import MultiProcessLogger, IMultiProcessLogger
from multiprocessing import Queue

if __name__ == "__main__":
    # TODO: implement a XML-configuration file
    db_file_name = "data/weather.db"
    data_directory = "C:\\Users\\Ralf\\Documents\\test"
    temp_data_directory = "C:\\Users\\Ralf\\Desktop\\temp"
    data_file_extension = ".ZIP"
    delta_time = 10     # time difference between two datasets (in minutes)
    log_file_name = "data/ftp_weather_server.log"

    with MultiProcessLogger(True, log_file_name) as logger:
        try:
            exception_queue = Queue()
            sql_database_service_factory = SQLDatabaseServiceFactory(db_file_name)

            # main server loop
            with FTPServerSideProxy(sql_database_service_factory, data_directory, data_file_extension, temp_data_directory, logger.get_connection_queue(), exception_queue, delta_time) as proxy:
                logger.log(IMultiProcessLogger.INFO, "Server is running.")
                
                # stall the main thread until the program is finished
                exception_from_subprocess = []
                try:
                    exception_from_subprocess = exception_queue.get()
                except KeyboardInterrupt:
                    pass

                if exception_from_subprocess:
                    exception_from_subprocess.re_raise()
        except Exception as e:
            logger.log(IMultiProcessLogger.ERROR, repr(e))

        logger.log(IMultiProcessLogger.INFO, "Server has stopped.")
