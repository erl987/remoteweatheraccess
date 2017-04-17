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

import os
import sys
import shutil
import unittest
from datetime import datetime
from zipfile import ZipFile

from scipy.misc import imread
from skimage import color
from skimage.measure import structural_similarity

from remote_weather_access.common.datastructures import CombiSensorData, BaseStationSensorData, RainSensorData, \
    WeatherStationMetadata
from remote_weather_access.common.fileformats import PCWetterstationFormatFile
from remote_weather_access.server import graphs
from remote_weather_access.server.sqldatabase import SQLWeatherDB


def sensors_to_plot():
    return [(BaseStationSensorData.BASE_STATION, BaseStationSensorData.PRESSURE),
            (RainSensorData.RAIN, RainSensorData.CUMULATED),
            ("IN", CombiSensorData.TEMPERATURE),
            ("IN", CombiSensorData.HUMIDITY)]


def combi_sensor():
    return "IN", "inside sensor 1"


def the_base_directory():
    return "./tests/workingDir/plotting"


def the_temp_data_directory():
    return the_base_directory() + os.sep + "temp"


def a_station_id():
    return "TES2"


def a_graph_file_name():
    return "graph.png"


def a_complete_graph_file_name():
    return the_base_directory() + os.sep + a_station_id() + os.sep + a_graph_file_name()


def expected_plot_file_name():
    test_data_dir = "./tests/testdata"
    expected_plot_file = "expected_plot.png"

    return test_data_dir + os.sep + sys.platform + os.sep + expected_plot_file


def a_data_file():
    return "./tests/testdata/150315_213115_1345_TES2.zip"


def image_similarity_index(image_1_path_name, image_2_path_name):
    """Calculates the similarity of two images. A structural similarity index of 1.0 means the images are identical."""
    image_1 = color.rgb2gray(imread(image_1_path_name))  # color-images are not supported in the version for Raspbian
    image_2 = color.rgb2gray(imread(image_2_path_name))

    similarity = structural_similarity(image_1, image_2)

    return similarity


def prepare_directories():
    if os.path.isdir(the_base_directory()):
        shutil.rmtree(the_base_directory(), ignore_errors=False)

    os.makedirs(the_base_directory(), exist_ok=True)
    os.makedirs(the_temp_data_directory())
    os.makedirs(the_base_directory() + os.sep + a_station_id())


def database_object():
    """Test database factory"""
    db_file_name = "sqltest.db"  # that database file should be unique for the tests

    db_file = the_base_directory() + os.sep + db_file_name

    sql_database = SQLWeatherDB(db_file)
    combi_sensor_id, combi_sensor_description = combi_sensor()
    sql_database.add_combi_sensor(combi_sensor_id, combi_sensor_description)
    sql_database.add_station(
        WeatherStationMetadata(a_station_id(), "TE923 Mebus", "Test City", 49.234, 11.024, 440, 1.0)
    )

    return sql_database, db_file


def load_data_in_database(sql_database: SQLWeatherDB):
    with ZipFile(a_data_file(), mode='r') as zip_file:
        data_file_list = zip_file.namelist()
        zip_file.extractall(the_temp_data_directory())

        # the ZIP-file must contain exactly one data file
        data_file_name = the_temp_data_directory() + os.sep + data_file_list[0]
        combi_sensor_id, combi_sensor_description = combi_sensor()
        weather_file = PCWetterstationFormatFile([combi_sensor_id], {combi_sensor_id: combi_sensor_description})

        data, rain_counter_base, station_metadata = weather_file.read(data_file_name, a_station_id(), 10.0)
        sql_database.add_dataset(station_metadata.get_station_id(), data)


class TestGraphGeneration(unittest.TestCase):
    def setUp(self):
        prepare_directories()
        self._sql_database, self._db_file_name = database_object()

    def tearDown(self):
        pass

    def test_plot_of_last_n_days(self):
        # given:
        image_similarity_threshold = 0.9999  # structural similarity index
        load_data_in_database(self._sql_database)

        # when:
        graphs.plot_of_last_n_days(7,
                                   self._db_file_name,
                                   a_station_id(),
                                   sensors_to_plot(),
                                   the_base_directory(),
                                   a_graph_file_name(),
                                   True,
                                   datetime(year=2015, month=3, day=3))

        # then:
        image_similarity = image_similarity_index(a_complete_graph_file_name(), expected_plot_file_name())
        self.assertTrue(image_similarity > image_similarity_threshold)


if __name__ == '__main__':
    unittest.main()
