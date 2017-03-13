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
import os

from remote_weather_access.common.logging import IMultiProcessLogger, MultiProcessLogger
from remote_weather_access.server import graphs
from remote_weather_access.server.config import WeatherPlotServiceIniFile
from remote_weather_access.server.sqldatabase import SQLWeatherDB
from remote_weather_access import __version__, package_name


def main():
    """
    Plotting the weather data for the requested station taking the data from a SQL-database.
    """
    parser = argparse.ArgumentParser(description="Plotting weather data from a SQL database.")
    parser.add_argument("ini_file", metavar="INI-FILE", type=str, help="configuration file")
    parser.add_argument("station_id", metavar="STATION-ID", type=str, help="station to be plotted: station ID or 'ALL'")
    parser.add_argument("--version", "-v", action="version", version="{} version {}".format(package_name, __version__),
                        help='show the version information of the program')

    args = parser.parse_args()

    try:
        entered_station_id = args.station_id
        config_file_name = args.ini_file

        config_file_handler = WeatherPlotServiceIniFile(config_file_name)
        configuration = config_file_handler.read()

        with MultiProcessLogger(True, configuration.get_log_config()) as logger:
            time_period_duration = configuration.get_plotter_settings().get_time_period_duration()
            graph_directory, graph_file_name = configuration.get_plotter_settings().get_graph_file_settings()

            try:
                # create plots for all requested stations
                if entered_station_id.upper() == "ALL":
                    weather_db = SQLWeatherDB(configuration.get_database_config().get_db_file_name())
                    chosen_station_ids = weather_db.get_stations()
                else:
                    chosen_station_ids = [entered_station_id]

                for station_id in chosen_station_ids:
                    # create the (sub-) directory of the plot if required
                    plot_dir_name = graph_directory + os.sep + station_id
                    try:
                        os.makedirs(plot_dir_name, exist_ok=True)
                    except Exception:
                        raise FileNotFoundError("The directory '{}' could not be created".format(plot_dir_name))

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
