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
from datetime import datetime
from weathernetwork.common.logging import IMultiProcessLogger, MultiProcessLogger
from weathernetwork.common.sensor import BaseStationSensorData, CombiSensorData, RainSensorData
from weathernetwork.server import graphs
from weathernetwork.server.config import LogConfig


def main():
    """Plotting the weather data for the requested station taking the data from a SQL-database.
    
    Commandline arguments: station_ID to be plotted, configuration INI-file
    """
    time_period_duration = 7  # number of days to be plotted
    db_file_name = "data/weather.db"
    data_storage_folder = ""
    sensors_to_plot = [BaseStationSensorData.PRESSURE,
                       (RainSensorData.RAIN, RainSensorData.CUMULATED),
                       ('OUT1', CombiSensorData.TEMPERATURE),
                       ('OUT1', CombiSensorData.HUMIDITY)]
    graph_directory = './data'
    graph_file_name = 'graph.svg'
    log_file_name = "./data/weatherDiagramPlotter.txt"
    max_kbytes_per_log_file = 100000
    max_num_log_files_to_keep = 0  # no file is deleted


    # read the command line arguments
    if len(sys.argv) != 3:
        print("Plotting weather data from a SQL database. Usage: python plot_weather_graph.py STATION_ID plot_config.ini")
    else:
        station_ID = sys.argv[1]
        config_file_name = sys.argv[2]

    log_config = LogConfig(log_file_name, max_kbytes_per_log_file, max_num_log_files_to_keep)
    with MultiProcessLogger(True, log_config) as logger:
        logger.log(IMultiProcessLogger.INFO, "Plotting last {} days for station {}.".format(time_period_duration, station_ID))
        num_plot_datasets, first_plot_time, last_plot_time = graphs.plot_of_last_n_days(
            time_period_duration, 
            db_file_name, 
            station_ID, 
            data_storage_folder, 
            sensors_to_plot, 
            graph_directory, 
            graph_file_name, 
            True, 
            datetime(year=2015, month=3, day=3)
        )
        logger.log(IMultiProcessLogger.INFO, "Plotting for station {} finished, plotted {} datasets ({} - {}).".format(
            station_ID, 
            num_plot_datasets, 
            first_plot_time,
            last_plot_time
        ))


if __name__ == "__main__":
    main()