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
import shutil
import json

from remote_weather_access.common.datastructures import WeatherStationMetadata
from remote_weather_access.server.sqldatabase import SQLWeatherDB
from remote_weather_access import __version__, package_name


def main():
    """
    Program for managing the stations being present in the weather database.
    """
    parser = argparse.ArgumentParser(description="Program for managing the stations being present in the weather "
                                                 "database. It automatically creates a new directory for receiving"
                                                 "data for the new station. WARNING: REMOVING A STATION FROM THE "
                                                 "DATABASE REMOVES ALL OF ITS DATA, THIS CANNOT BE UNDONE.")
    parser.add_argument("db_file", metavar="DATABASE", type=str, help="weather database")

    operation_type = parser.add_mutually_exclusive_group(required=True)
    operation_type.add_argument("--print", "-p", dest="do_print", action="store_true",
                                help="print all combi sensors present in the database")
    operation_type.add_argument("--add", "-a", metavar="STATION-DATA-FILE", type=str,
                                help="add new stations specified in the JSON-file (containing "
                                     "{\"metadata\": \"description\", ...})")
    operation_type.add_argument("--remove", "-rm", metavar="STATION-ID", type=str,
                                help="remove the specified station")
    operation_type.add_argument("--replace", "-rp", metavar="STATION-DATA-FILE", type=str,
                                help="replace the station metadata by that specified in the JSON-file (containing "
                                     "{\"metadata\": \"description\", ...})")

    parser.add_argument("--receiver-directory", "-recv", metavar="RECEIVER-DIRECTORY", type=str,
                        default="/var/lib/remote-weather-access/receiver",
                        help="base directory of the subdirectory where the data files are provided by the FTP-server "
                             "(default: /var/lib/remote-weather-access/receiver)")
    parser.add_argument("--user", "-u", metavar="USER", type=str, default="weather-daemon",
                        help="user running the weather server process (default: weather-daemon)")
    parser.add_argument("--group", "-g", metavar="GROUP", type=str, default="weather-daemon",
                        help="group of the user running the weather server process (default: weather-daemon)")

    parser.add_argument("--version", "-v", action="version", version="{} version {}".format(package_name, __version__),
                        help='show the version information of the program')

    args = parser.parse_args()

    try:
        db_file_name = args.db_file
        station_metadata = None
        station_id = None
        json_metadata_file = None

        if args.add:
            json_metadata_file = args.add
        if args.replace:
            json_metadata_file = args.replace

        if json_metadata_file:
            # read the station metadata
            with open(json_metadata_file) as file:
                metadata = json.load(file)
                station_metadata = WeatherStationMetadata(metadata["station_id"],
                                                          metadata["device_info"],
                                                          metadata["location_info"],
                                                          metadata["latitude"],
                                                          metadata["longitude"],
                                                          metadata["height"],
                                                          metadata["rain_calib_factor"])
        if args.remove:
            station_id = args.remove

        # update the database
        database = SQLWeatherDB(db_file_name)
        if args.add:
            database.add_station(station_metadata)
            station_dir_name = args.receiver_directory + os.sep + station_metadata.get_station_id()
            try:
                os.makedirs(station_dir_name, exist_ok=True)
                shutil.chown(station_dir_name, args.user, args.group)
                os.chmod(station_dir_name, 0o775)  # the group requires write access (i.e. the FTP-server)
            except Exception as e:
                print("WARNING: The directory '{}' could not be created: {}".format(station_dir_name, e))
        elif args.replace:
            database.replace_station(station_metadata)
        elif args.remove:
            if not database.remove_station(station_id):
                raise SyntaxError("The station {} does not exist in the database".format(station_id))

            station_dir_name = args.receiver_directory + os.sep + station_id
            try:
                os.rmdir(station_dir_name)
            except Exception as e:
                print("WARNING: The directory '{}' could not be deleted: {}".format(station_dir_name, e))
        elif args.do_print:
            station_ids = database.get_stations()

            print("Stations in the database:\n")
            if station_ids:
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
                print("None")
        else:
            raise SyntaxError("Invalid command arguments")

        print("Operation was successful.")
    except Exception as e:
        print("Execution failed: {}. Call the command with the option --help for support.".format(e))


if __name__ == "__main__":
    main()
