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
import json

from remote_weather_access.server.sqldatabase import SQLWeatherDB
from remote_weather_access import __version__, package_name


def main():
    """
    Program for managing the combi sensors (temperature / humidity) being present in the weather database.
    """
    parser = argparse.ArgumentParser(description="Program for managing the combi sensors (temperature / humidity) "
                                                 "being present in the weather database. WARNING: REMOVING A SENSOR "
                                                 "FROM THE DATABASE REMOVES ALL OF ITS DATA, THIS CANNOT BE UNDONE.")
    parser.add_argument("db_file", metavar="DATABASE", type=str, help="weather database")
    operation_type = parser.add_mutually_exclusive_group(required=True)
    operation_type.add_argument("--print", "-p", dest="do_print", action="store_true",
                                help="print all combi sensors present in the database")
    operation_type.add_argument("--add", "-a", metavar="SENSOR-DATA-FILE", type=str,
                                help="add new sensors specified in the JSON-file (containing "
                                     "{\"SENSOR-ID\": \"description\", ...})")
    operation_type.add_argument("--remove", "-rm", metavar="SENSOR-ID", type=str,
                                help="remove the specified sensor")
    operation_type.add_argument("--replace", "-rp", metavar="SENSOR-DATA-FILE", type=str,
                                help="replace the sensor data by that specified in the JSON-file (containing "
                                     "{\"SENSOR-ID\": \"description\", ...})")
    parser.add_argument("--version", "-v", action="version", version="{} version {}".format(package_name, __version__),
                        help='show the version information of the program')

    args = parser.parse_args()

    try:
        db_file_name = args.db_file
        sensor_data = None
        sensor_id = None
        json_metadata_file = None

        if args.add:
            json_metadata_file = args.add
        if args.replace:
            json_metadata_file = args.replace
        if json_metadata_file:
            with open(json_metadata_file) as file:
                sensor_data = json.load(file)
        if args.remove:
            sensor_id = args.remove

        # update the database
        database = SQLWeatherDB(db_file_name)
        if args.add:
            for sensor_id in sensor_data:
                database.add_combi_sensor(sensor_id, sensor_data[sensor_id])
        elif args.replace:
            for sensor_id in sensor_data:
                database.replace_combi_sensor(sensor_id, sensor_data[sensor_id])
        elif args.remove:
            if not database.remove_combi_sensor(sensor_id):
                raise SyntaxError("The sensor {} does not exist in the database".format(sensor_id))
        elif args.do_print:
            sensor_ids, sensor_descriptions = database.get_combi_sensors()
            print("Combi sensors present in the database:\n")
            if sensor_ids:
                for sensor_id in sensor_ids:
                    print(sensor_id + ": " + sensor_descriptions[sensor_id])
            else:
                print("None")
        else:
            raise SyntaxError("Invalid command arguments")

        if not args.do_print:
            print("You must restart the weather server now to reload the available stations.")
        print("\nOperation was successful.")
    except Exception as e:
        print("Execution failed: {}. Call the command without options for help.".format(e))


if __name__ == "__main__":
    main()
