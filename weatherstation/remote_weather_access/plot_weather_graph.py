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
import os
import sys
from pathlib import Path

from remote_weather_access.common.logging import IMultiProcessLogger, MultiProcessLogger
from remote_weather_access.server import graphs
from remote_weather_access.server.config import WeatherPlotServiceIniFile


def main():
    """
    Plotting the weather data for the requested station taking the data from a SQL-database.
    
    Commandline arguments:
    station_ID to be plotted, configuration INI-file

    Usage:
    python plot_weather_graph.py STATION_ID plot_config.ini
    """
    # read the command line arguments
    if len(sys.argv) != 3:
        print("Plotting weather data from a SQL database. Usage: weatherplot STATION_ID plot_config.ini")
    else:
        try:
            station_id = sys.argv[1]
            config_file_name = sys.argv[2]

            config_file_handler = WeatherPlotServiceIniFile(config_file_name)
            configuration = config_file_handler.read()

            with MultiProcessLogger(True, configuration.get_log_config()) as logger:
                time_period_duration = configuration.get_plotter_settings().get_time_period_duration()
                graph_directory, graph_file_name = configuration.get_plotter_settings().get_graph_file_settings()

                try:
                    # create the (sub-) directory of the plot if required
                    plot_dir_path = Path(graph_directory + os.sep + station_id)
                    try:
                        plot_dir_path.mkdir(exist_ok=True, parents=True)
                    except Exception:
                        raise FileNotFoundError("The directory '{}' could not be created".format(plot_dir_path))

                    logger.log(IMultiProcessLogger.INFO, "Started plotting the last {} days for station {}.".format(
                        time_period_duration, station_id))
                    num_plot_datasets, first_plot_time, last_plot_time = graphs.plot_of_last_n_days(
                        time_period_duration,
                        configuration.get_database_config().get_db_file_name(),
                        station_id,
                        configuration.get_plotter_settings().get_sensors_to_plot(),
                        graph_directory,
                        graph_file_name,
                        True
                    )
                    logger.log(
                        IMultiProcessLogger.INFO,
                        "Finished plotting for station {}, plotted {} datasets ({} - {}).".format(
                            station_id,
                            num_plot_datasets,
                            first_plot_time,
                            last_plot_time
                        )
                    )
                except Exception as e:
                    logger.log(IMultiProcessLogger.ERROR, repr(e))
        except Exception as e:
            print("An exception occurred: {}".format(e))


if __name__ == "__main__":
    main()
