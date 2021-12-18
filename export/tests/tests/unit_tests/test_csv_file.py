#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2021 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
import copy
import os.path
import pathlib

import pytest

from export_src.backend_requests import reformat_sensor_metadata, reformat_station_metadata
from export_src.csv_file import create_pc_weatherstation_compatible_file
from tests.tests.utils import csv_files_do_match

STATION_ID = 'TES'
MONTH = 9
YEAR = 2021
STATION_METADATA = [{'device': 'TE923',
                     'height': 1256.0,
                     'id': 5,
                     'latitude': 29.97162,
                     'location': 'Test City/TE/AN',
                     'longitude': 31.51835,
                     'rain_calib_factor': 0.6820802083333333,
                     'station_id': 'TES'}]

SENSOR_METADATA = [{'description': 'UV', 'sensor_id': 'uv', 'unit': 'UV-X'},
                   {'description': 'Regen', 'sensor_id': 'rain', 'unit': 'mm'},
                   {'description': 'Regenrate', 'sensor_id': 'rain_rate', 'unit': 'mm'},
                   {'description': 'Temperatur', 'sensor_id': 'temperature', 'unit': '\u00b0C'},
                   {'description': 'Luftfeuchte', 'sensor_id': 'humidity', 'unit': '%'},
                   {'description': 'Windgeschwindigkeit', 'sensor_id': 'speed', 'unit': 'km/h'},
                   {'description': 'Windb\u00f6en', 'sensor_id': 'gusts', 'unit': 'km/h'},
                   {'description': 'Windrichtung', 'sensor_id': 'direction', 'unit': '\u00b0'},
                   {'description': 'Windchilltemperatur', 'sensor_id': 'wind_temperature', 'unit': '\u00b0C'},
                   {'description': 'Luftdruck', 'sensor_id': 'pressure', 'unit': 'hPa'}]

MONTH_DATA = {
    'TES': {
        'timepoint': ['2021-12-01T00:00:00+01:00', '2021-12-01T00:10:00+01:00', '2021-12-01T00:20:00+01:00',
                      '2021-12-01T00:30:00+01:00', '2021-12-01T00:40:00+01:00', '2021-12-01T00:50:00+01:00',
                      '2021-12-01T01:00:00+01:00', '2021-12-01T01:10:00+01:00', '2021-12-01T01:20:00+01:00',
                      '2021-12-01T01:30:00+01:00', '2021-12-01T01:40:00+01:00', '2021-12-01T01:50:00+01:00'],
        'pressure': [1010.3, 1010.3, 1010.6, 1010.6, 1011.5, 1011.5, 1011.2, 1011.2, 1010.7, 1010.7, 1010.4, 1010.4],
        'uv': [8.7, 9.3, 8.3, 6.5, 4.3, 6.5, 7.4, 10.5, 8.9, 7.7, 6.5, 6.2],
        'speed': [50.6, 43.1, 53.2, 61.5, 65.3, 50.2, 43.5, 30.1, 21.5, 25.9, 19.3, 15.3],
        'gusts': [80.3, 79.1, 60.9, 69.5, 75.5, 81.9, 60.5, 40.1, 30.9, 35.3, 25.1, 18.6],
        'wind_temperature': [3.6, 3.6, 3.7, 3.7, 3.9, 3.9, 3.8, -0.7, -2.9, -2.5, 3.8, 3.1],
        'direction': [350.1, 5.2, 120.5, 80.5, 10.5, 20.3, 30.4, 25.3, 160.5, 180.5, 210.5, 190.5],
        'rain': [0.0, 0.0, 0.0, 0.0, 0.0, 0.6820802083333333, 0.6820802083333333, 0.6820802083333333,
                 0.6820802083333333, 1.3641604166666665, 1.3641604166666665, 1.3641604166666665],
        'rain_rate': [0.0, 0.0, 0.0, 0.0, 0.0, 0.6820802083333333, 0.0, 0.0, 0.0, 0.6820802083333333, 0.0, 0.0],
        'temperature_humidity': {
            'IN': {
                'humidity': [40.0, 40.0, 39.0, 37.0, 36.0, 36.0, 36.0, 36.0, 36.0, 37.0, 37.0, 38.0],
                'temperature': [20.8, 20.9, 21.9, 22.65, 23.0, 23.05, 22.95, 22.7, 22.45, 22.15, 21.8, 21.5]
            },
            'OUT1': {
                'humidity': [86.0, 86.0, 86.0, 86.0, 86.0, 86.0, 85.0, 85.0, 85.0, 84.0, 84.0, 83.0],
                'temperature': [3.4, 3.4, 3.5, 3.5, 3.5, 3.5, 3.4, -0.5, -2.5, -2.1, 3.5, 3.5]
            }
        }
    }
}

REFERENCE_DATA_PATH = r'./reference_data'
EXPECTED_FILE_NAME = 'EXP09_21.csv'

base_path = pathlib.Path(__file__).parent.resolve()


def test_write_csv_file(tmpdir):
    destination_dir = tmpdir.mkdir('csv_files')
    created_csv_file_path = create_pc_weatherstation_compatible_file(MONTH_DATA, STATION_ID, MONTH, YEAR,
                                                                     reformat_sensor_metadata(SENSOR_METADATA),
                                                                     reformat_station_metadata(STATION_METADATA,
                                                                                               STATION_ID)[0],
                                                                     destination_dir)

    reference_csv_file_path = os.path.join(base_path, REFERENCE_DATA_PATH, r'./regular', EXPECTED_FILE_NAME)

    assert os.path.basename(created_csv_file_path) == EXPECTED_FILE_NAME
    assert csv_files_do_match(created_csv_file_path, reference_csv_file_path)


def test_write_csv_file_when_no_temperature_humidity_data(tmpdir):
    month_data_without_temp_humidity = copy.deepcopy(MONTH_DATA)
    del month_data_without_temp_humidity['TES']['temperature_humidity']

    destination_dir = tmpdir.mkdir('csv_files')
    created_csv_file_path = create_pc_weatherstation_compatible_file(month_data_without_temp_humidity, STATION_ID,
                                                                     MONTH, YEAR,
                                                                     reformat_sensor_metadata(SENSOR_METADATA),
                                                                     reformat_station_metadata(STATION_METADATA,
                                                                                               STATION_ID)[0],
                                                                     destination_dir)

    reference_csv_file_path = os.path.join(base_path, REFERENCE_DATA_PATH, r'./when_no_temp_humid', EXPECTED_FILE_NAME)

    assert os.path.basename(created_csv_file_path) == EXPECTED_FILE_NAME
    assert csv_files_do_match(created_csv_file_path, reference_csv_file_path)


def test_write_empty_data_to_csv_file(tmpdir):
    destination_dir = tmpdir.mkdir('csv_files')
    created_csv_file_path = create_pc_weatherstation_compatible_file({}, STATION_ID, MONTH, YEAR,
                                                                     reformat_sensor_metadata(SENSOR_METADATA),
                                                                     reformat_station_metadata(STATION_METADATA,
                                                                                               STATION_ID)[0],
                                                                     destination_dir)
    assert created_csv_file_path is None


def test_too_many_temperature_sensors(tmpdir):
    destination_dir = tmpdir.mkdir('csv_files')

    month_data_with_too_many_temp_sensors = copy.deepcopy(MONTH_DATA)
    for i in range(2, 17):
        month_data_with_too_many_temp_sensors['TES']['temperature_humidity'][f'OUT{i}'] = \
            MONTH_DATA['TES']['temperature_humidity']['OUT1']

    with pytest.raises(ValueError):
        create_pc_weatherstation_compatible_file(month_data_with_too_many_temp_sensors, STATION_ID,
                                                 MONTH, YEAR,
                                                 reformat_sensor_metadata(SENSOR_METADATA),
                                                 reformat_station_metadata(STATION_METADATA, STATION_ID)[0],
                                                 destination_dir)


def test_too_many_humidity_sensors(tmpdir):
    destination_dir = tmpdir.mkdir('csv_files')

    month_data_with_too_many_temp_sensors = copy.deepcopy(MONTH_DATA)
    for i in range(2, 17):
        month_data_with_too_many_temp_sensors['TES']['temperature_humidity'][f'OUT{i}'] = \
            copy.deepcopy(MONTH_DATA['TES']['temperature_humidity']['OUT1'])

    del month_data_with_too_many_temp_sensors['TES']['temperature_humidity']['OUT16']['temperature']

    with pytest.raises(ValueError):
        create_pc_weatherstation_compatible_file(month_data_with_too_many_temp_sensors, STATION_ID,
                                                 MONTH, YEAR,
                                                 reformat_sensor_metadata(SENSOR_METADATA),
                                                 reformat_station_metadata(STATION_METADATA, STATION_ID)[0],
                                                 destination_dir)
