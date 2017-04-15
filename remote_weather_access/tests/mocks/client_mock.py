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
import datetime
import os
import random
import shutil
import time
from zipfile import ZipFile

from remote_weather_access.server.exceptions import NotExistingError
from remote_weather_access.common.fileformats import PCWetterstationFormatFile
from remote_weather_access.common.datastructures import WeatherStationDataset, BaseStationSensorData, WindSensorData, \
    CombiSensorData, RainSensorData
from remote_weather_access.server.sqldatabase import SQLWeatherDB

station_ids = ["NBG", "ERL", "ECK"]
receiver_base_dirpath = "/var/lib/remote-weather-access/receiver"
temp_dir_path = "/tmp"
db_file_name = "/var/lib/remote-weather-access/weather.db"
archive_file_type = "zip"
data_file_type = "csv"

min_delay_time = 0.5  # in seconds
max_delay_time = 60   # in seconds


def random_delay_time():
    """Creates a random delay time for the next data sending to the server."""
    return random.uniform(min_delay_time, max_delay_time)


def main():
    """
    Mock client for sending test data to the weatherserver (by mocking FTP-file transfer on the local machine).

    Usage:
    install in "/usr/lib/python3/dist-packages/remote_weather_access"
    run by installing the systemd-service "clientmock"
    """
    # determine the first time based on the earliest last database entry
    database = SQLWeatherDB(db_file_name)
    next_times = []
    for station_id in station_ids:
        try:
            next_times.append(database.get_most_recent_time_with_data(station_id) + datetime.timedelta(minutes=10))
        except NotExistingError:
            pass
    next_time = min(next_times)

    # load the station metadata from the database
    station_metadata = dict()
    for station_id in station_ids:
        station_metadata[station_id] = database.get_station_metadata(station_id)

    # load the combi sensor descriptions from the database
    combi_sensor_ids, combi_sensor_descriptions = database.get_combi_sensors()

    while True:
        for station_id in station_ids:
            # create data
            dataset = WeatherStationDataset(next_time)
            dataset.add_sensor(BaseStationSensorData(1032.4, 8.5))
            dataset.add_sensor(WindSensorData(12.4, 43.9, 180.0, 15.2))
            for combi_id in combi_sensor_ids:
                dataset.add_sensor(CombiSensorData(combi_id, 34.9, 89.7, combi_sensor_descriptions[combi_id]))
            dataset.add_sensor(RainSensorData(12.5, next_time - datetime.timedelta(minutes=10)))
            data = [dataset]

            archive_file_name = None
            curr_temp_dir_path = None
            try:
                # create a new temporary directory
                curr_time_string = str(datetime.datetime.utcnow().timestamp())
                curr_time_string = curr_time_string.replace(".", "_")
                curr_temp_dir_path = temp_dir_path + os.sep + curr_time_string
                os.mkdir(curr_temp_dir_path)

                weather_data_file = PCWetterstationFormatFile(combi_sensor_ids, combi_sensor_descriptions)
                weather_data_file.write(curr_temp_dir_path, data, station_metadata[station_id])

                # copy the data file to the weather server receiver directory for consumption
                archive_file_name = temp_dir_path + os.sep + curr_time_string + "_" + station_id + "." +\
                                    archive_file_type
                with ZipFile(archive_file_name, mode='w') as archive:
                    for file in os.listdir(curr_temp_dir_path):
                        if file.upper().endswith(data_file_type.upper()):
                            archive.write(os.path.join(curr_temp_dir_path, file), file)

                receiver_dir_path = receiver_base_dirpath + os.sep + station_id
                shutil.copy(archive_file_name, receiver_dir_path)
            finally:
                if archive_file_name and os.path.exists(archive_file_name):
                    os.remove(archive_file_name)
                if curr_temp_dir_path:
                    shutil.rmtree(curr_temp_dir_path, ignore_errors=True)

        next_time += datetime.timedelta(minutes=10)
        time.sleep(random_delay_time())


if __name__ == "__main__":
    main()
