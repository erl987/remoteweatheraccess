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
import json

from remote_weather_access.common.datastructures import WeatherStationMetadata
from remote_weather_access.server.sqldatabase import SQLWeatherDB


def main():
    """
    Program for managing the stations being present in the weather database.
    """
    if len(sys.argv) != 4 and not (len(sys.argv) == 3 and sys.argv[-1].upper() == "PRINT"):
        print("Invalid number of arguments.\n"
              "\n"
              "Program for managing the stations being present in the weather database.\n"
              "WARNING: REMOVING A STATION FROM THE DATABASE REMOVES ALL OF ITS DATA, THIS CANNOT BE UNDONE."
              "\n"
              "Command line arguments:\n"
              "manage-weather-stations [DB_FILE] [PRINT] | [[TYPE] [JSON-FILE|STATION ID]]\n"
              "\n"
              "DB_FILE: path of the weather database file\n"
              "PRINT: prints all combi sensors present in the database\n"
              "TYPE: type of operation (add | remove | replace)\n"
              "JSON-FILE: containing all required settings for the added / replaced station\n"
              "\n"
              "Example usages:\n"
              "manage-weather-stations ./weather.db add newStation.json\n"
              "manage-weather-stations ./weather.db remove TES2\n"
              "manage-weather-stations ./weather.db replace newStation.json\n"
              "manage-weather-stations ./weather.db print\n"
              "\n"
              "Necessary format for the JSON-file:\n"
              "{\n"
              "     \"station_id\": \"NBG\",\n",
              "     \"device_info\": \"TE923\",\n",
              "     \"location_info\": \"Nürnberg\",\n",
              "     \"latitude\": 49.374,\n",
              "     \"longitude\": 11.017,\n",
              "     \"height\": 330,\n",
              "     \"rain_calib_factor\": 1.0\n"
              "}")
    else:
        try:
            db_file_name = sys.argv[1]
            operation_type = sys.argv[2].upper()
            station_metadata = None
            station_id = None

            if operation_type == "ADD" or operation_type == "REPLACE":
                # read the station metadata
                json_metadata_file = sys.argv[3]
                with open(json_metadata_file) as file:
                    metadata = json.load(file)
                    station_metadata = WeatherStationMetadata(metadata["station_id"],
                                                              metadata["device_info"],
                                                              metadata["location_info"],
                                                              metadata["latitude"],
                                                              metadata["longitude"],
                                                              metadata["height"],
                                                              metadata["rain_calib_factor"])
            elif operation_type == "REMOVE":
                station_id = sys.argv[3]

            # update the database
            database = SQLWeatherDB(db_file_name)
            if operation_type == "ADD":
                database.add_station(station_metadata)
            elif operation_type == "REPLACE":
                database.replace_station(station_metadata)
            elif operation_type == "REMOVE":
                if not database.remove_station(station_id):
                    raise SyntaxError("The station {} does not exist in the database".format(station_id))
            elif operation_type == "PRINT":
                station_ids = database.get_stations()

                print("Stations in the database:\n")
                for station_id in station_ids:
                    station_metadata = database.get_station_metadata(station_id)

                    device_info = station_metadata.get_device_info()
                    location_info = station_metadata.get_location_info()
                    latitude, longitude, height = station_metadata.get_geo_info()
                    print(station_id + ": "
                          + location_info + ", "
                          + device_info + " ("
                          + str(latitude) + "\N{DEGREE SIGN}, "
                          + str(longitude) + "\N{DEGREE SIGN}, "
                          + str(height) + " m)")
            else:
                raise SyntaxError("Invalid command arguments")

            print("Operation was successful.")
        except Exception as e:
            print("Execution failed: {}. Call the command without options for help.".format(e))


if __name__ == "__main__":
    main()
