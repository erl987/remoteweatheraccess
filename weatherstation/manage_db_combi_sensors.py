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

from weathernetwork.server.sqldatabase import SQLWeatherDB


# TODO: functionality for getting the existing stations / sensors is missing ....
# TODO: it should be possible to remove more than one sensor at once
def main():
    """
    Program for managing the combi sensors (temperature / humidity) being present in the weather database.
    """
    if len(sys.argv) != 4 and not (len(sys.argv) == 3 and sys.argv[-1] == "PRINT"):
        print("Invalid number of arguments.\n"
              "\n"
              "Program for managing the combi sensors (temperature / humidity) being present in the weather "
              "database.\n"
              "WARNING: REMOVING A SENSOR FROM THE DATABASE REMOVES ALL OF ITS DATA, THIS CANNOT BE UNDONE."
              "\n"
              "Command line arguments:\n"
              "python manage_db_combi_sensors.py [DB_FILE] [PRINT] | [[TYPE] [JSON-FILE|SENSOR ID...]]\n"
              "\n"
              "DB_FILE: path of the weather database file"
              "PRINT: prints all combi sensors present in the database"
              "TYPE: type of operation (add | remove | replace)\n"
              "JSON-FILE: containing all required settings for the added / replaced sensors\n"
              "\n"
              "Example usages:\n"
              "python ftp_weather_server.py ./weather.db add newSensors.json\n"
              "python ftp_weather_server.py ./weather.db remove OUT1\n"
              "python ftp_weather_server.py ./weather.db replace newSensors.json\n"
              "python ftp_weather_server.py print\n"
              "\n"
              "Necessary format for the JSON-file:\n"
              "{\n"
              "     \"IN\": \"Innensensor\",\n",
              "     \"OUT\": \"Außensensor 1\",\n"
              "}")
    else:
        db_file_name = sys.argv[1]
        operation_type = sys.argv[2].upper()
        sensor_data = None
        sensor_id = None

        try:
            if operation_type == "ADD" or operation_type == "REPLACE":
                json_metadata_file = sys.argv[3]
                with open(json_metadata_file) as file:
                    sensor_data = json.load(file)
            elif operation_type == "REMOVE":
                sensor_id = sys.argv[3]

            # update the database
            database = SQLWeatherDB(db_file_name)
            if operation_type == "ADD":
                for sensor_id in sensor_data:
                    database.add_combi_sensor(sensor_id, sensor_data[sensor_id])
            elif operation_type == "REPLACE":
                for sensor_id in sensor_data:
                    database.replace_combi_sensor(sensor_id, sensor_data[sensor_id])
            elif operation_type == "REMOVE":
                if not database.remove_combi_sensor(sensor_id):
                    raise SyntaxError("The sensor {} does not exist in the database".format(sensor_id))
            elif operation_type == "PRINT":
                sensor_ids, sensor_descriptions = database.get_combi_sensors()
                print("Combi sensors present in the database:\n")
                for sensor_id in sensor_ids:
                    print(sensor_id + ": " + sensor_descriptions[sensor_id])
            else:
                raise SyntaxError("Invalid command arguments")

            print("\nOperation was successful.")
        except Exception as e:
            print("Execution failed: {}. Call the command without options for help.".format(e))


if __name__ == "__main__":
    main()
