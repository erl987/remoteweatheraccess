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

from remote_weather_access import __version__, package_name
from remote_weather_access.common.fileformats import PCWetterstationFormatFile
from remote_weather_access.common.logging import IMultiProcessLogger
from remote_weather_access.common.logging import MultiProcessLogger
from remote_weather_access.common.utilities import get_first_day_of_month, get_last_day_of_month, \
    a_day_in_previous_month
from remote_weather_access.server.config import ExportServiceIniFile, ExportConfigSection
from remote_weather_access.server.sqldatabase import SQLWeatherDB


def get_parameters(config_file):
    """
    Obtains the program parameters from the configuration file.
    """
    config_file_handler = ExportServiceIniFile(config_file)
    configuration = config_file_handler.read()

    db_file_name = configuration.get_database_config().get_db_file_name()
    export_section = configuration.get_export_settings()

    output_path = export_section.get_export_directory()
    station_id = export_section.get_station_id()
    first_month, last_month = export_section.get_time_period()

    first_day = get_first_day_of_month(first_month)
    last_day = get_last_day_of_month(last_month)

    return db_file_name, output_path, station_id, first_day, last_day, configuration


def generate_export_file(database, db_file_name, station_id, first_day, last_day, output_path, logger):
    """
    Creates the export data file for a single station.
    """
    if first_day == ExportConfigSection.INVALID_DATE:
        latest_date = database.get_most_recent_time_with_data(station_id)
        first_day = get_first_day_of_month(a_day_in_previous_month(latest_date))
        last_day = get_last_day_of_month(latest_date)

    data = database.get_data_in_time_range(station_id, first_day, last_day)
    combi_sensor_ids, combi_sensor_descriptions = database.get_combi_sensors()
    station_metadata = database.get_station_metadata(station_id)

    # create the subdirectory for the station data if required
    station_output_path = output_path + os.sep + station_id
    os.makedirs(station_output_path, exist_ok=True)

    # create automatically all required monthly data files
    if data:
        export_file = PCWetterstationFormatFile(combi_sensor_ids, combi_sensor_descriptions)
        export_file.write(station_output_path, data, station_metadata)
        logger.log(IMultiProcessLogger.INFO, "Successfully wrote data for the station '{}' "
                                             "in the period {} - {}".format(station_id,
                                                                            first_day,
                                                                            last_day.replace(microsecond=0)))
    else:
        logger.log(IMultiProcessLogger.ERROR, "The database '{}' contains no data for the station '{}' "
                                              "in the period {} - {}".format(db_file_name,
                                                                             station_id,
                                                                             first_day,
                                                                             last_day.replace(microsecond=0)))


def main():
    """
    Exporting weather data from the SQL-database into PCWetterstation format files.
    """
    parser = argparse.ArgumentParser(description="Exporting weather data from the SQL-database into PCWetterstation "
                                                 "format files.")
    parser.add_argument("ini_file", metavar="INI-FILE", type=str, help="configuration file")
    parser.add_argument("--version", "-v", action="version", version="{} version {}".format(package_name, __version__),
                        help='show the version information of the program')

    try:
        args = parser.parse_args()
        db_file_name, output_path, station_id, first_day, last_day, configuration = get_parameters(args.ini_file)

        with MultiProcessLogger(True, configuration.get_log_config()) as logger:
            try:
                if not os.path.isfile(db_file_name):
                    raise FileNotFoundError("The database file '{}' does not exist".format(db_file_name))
                if not os.path.exists(output_path):
                    raise NotADirectoryError("The output directory '{}' does not exist".format(output_path))

                database = SQLWeatherDB(db_file_name)
                if station_id == ExportConfigSection.ALL_STATIONS:
                    all_station_ids = database.get_stations()
                else:
                    all_station_ids = [station_id]

                # initial logging
                if station_id == ExportConfigSection.ALL_STATIONS:
                    station_text_str = "the stations {}".format(all_station_ids)
                else:
                    station_text_str = "station '{}'".format(station_id)
                if first_day == ExportConfigSection.INVALID_DATE:
                    period_text_str = "last two months"
                else:
                    period_text_str = "period {} - {}".format(first_day, last_day)

                logger.log(IMultiProcessLogger.INFO, "Started exporting the data of {}"
                           " in the {} to the base directory '{}'".format(station_text_str, period_text_str,
                                                                          output_path))

                # export the requested data
                for curr_station_id in all_station_ids:
                    try:
                        generate_export_file(database, db_file_name, curr_station_id, first_day, last_day, output_path,
                                             logger)
                    except Exception as e:
                        logger.log(IMultiProcessLogger.ERROR, "Error while processing data for station '{}': {}".
                                   format(curr_station_id, str(e)))
            except Exception as e:
                logger.log(IMultiProcessLogger.ERROR, str(e))
    except Exception as e:
        print("An error occurred: {}".format(e))


if __name__ == "__main__":
    main()
