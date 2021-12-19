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
import logging
import os

import numpy as np
import pandas as pd

# mapping the sensor ids to the PCWetterstation file format based sensor IDs
# (see page 269 of the manual for PCWetterstation)
PC_WETTERSTATION_GENERAL_MAPPING = {
    'pressure': 133,
    'uv': 9,
    'speed': 35,
    'gusts': 45,
    'wind_temperature': 8,
    'direction': 36,
    'rain_rate': 34,
}

PC_WETTERSTATION_TEMP_MAPPING = {'min': 1, 'max': 16}
PC_WETTERSTATION_HUMID_MAPPING = {'min': 17, 'max': 32}

MAX_NUM_DECIMALS = 5
DATE_DUMMY_SENSOR_ID = -20  # can be any negative value, just for ordering the sensor columns
TIME_DUMMY_SENSOR_ID = -19  # can be any negative value, just for ordering the sensor columns

logger = logging.getLogger('exporter')


# noinspection PyTypeChecker
def create_pc_weatherstation_compatible_file(month_data_in, station_id, month, year, sensor_metadata, station_metadata,
                                             destination_dir):
    month_data = copy.deepcopy(month_data_in)
    csv_file_name = 'EXP{:02d}_{}.csv'.format(month, str(year)[-2:])
    csv_file_path = os.path.join(destination_dir, csv_file_name)

    if len(month_data) > 0:
        logger.debug('Data for station {} contains {} entries'.format(station_id,
                                                                      len(month_data[station_id]['timepoint'])))

        df = _create_data_frame(month_data, station_id)

        pc_wetterstation_sensor_ids, sensor_names, sensor_units, station_metadata_line = \
            _process_metadata(df, sensor_metadata, station_metadata)

        sorted_indices = np.argsort(pc_wetterstation_sensor_ids)

        header_1_df, header_2_df = _create_header_data_frames(pc_wetterstation_sensor_ids, sensor_names, sensor_units,
                                                              sorted_indices)

        df.columns = sensor_names
        df = df.reindex(columns=df.columns[sorted_indices])

        df = df.round(MAX_NUM_DECIMALS)

        # PC-Wetterstation requires Windows line endings
        with open(csv_file_path, 'w', newline='\r\n') as csv_file:
            header_1_df.to_csv(csv_file, index=False)
            csv_file.write(station_metadata_line)
            header_2_df.to_csv(csv_file, index=False, header=False)
            df.to_csv(csv_file, index=False, header=False)

        return csv_file_path
    else:
        logger.debug('Data for station {} is empty'.format(station_id))
        return None


def _create_header_data_frames(pc_wetterstation_sensor_ids, sensor_names, sensor_units, sorted_indices):
    header_1_df = pd.DataFrame([sensor_units], columns=sensor_names)
    header_2_df = pd.DataFrame([pc_wetterstation_sensor_ids], columns=sensor_names)

    # sort by the sensor indices
    header_1_df = header_1_df.reindex(columns=header_1_df.columns[sorted_indices])
    header_2_df = header_2_df.reindex(columns=header_2_df.columns[sorted_indices])

    # remove the dummy sensor indices for date and time
    header_2_df.iloc[0, 0] = ''
    header_2_df.iloc[0, 1] = ''

    return header_1_df, header_2_df


def _create_data_frame(month_data, station_id):
    if 'temperature_humidity' in month_data[station_id]:
        temp_humidity_data = month_data[station_id]['temperature_humidity']
        del month_data[station_id]['temperature_humidity']
    else:
        temp_humidity_data = {}

    df = pd.DataFrame.from_dict(month_data[station_id])
    for sensor_id in temp_humidity_data:
        if 'temperature' in temp_humidity_data[sensor_id]:
            df['temperature_{}'.format(sensor_id)] = temp_humidity_data[sensor_id]['temperature']
        if 'humidity' in temp_humidity_data[sensor_id]:
            df['humidity_{}'.format(sensor_id)] = temp_humidity_data[sensor_id]['humidity']

    if 'rain' in df:
        df.drop('rain', axis=1, inplace=True)  # only the rain rate is relevant

    # reformat the time points
    # TODO: this needs to be generalized ...
    df['timepoint'] = df['timepoint'].str.replace('\+02:00', ' ')
    df['timepoint'] = df['timepoint'].str.replace('\+01:00', ' ')

    df['date'] = pd.to_datetime(df['timepoint']).dt.strftime('%d.%m.%Y')
    df['time'] = pd.to_datetime(df['timepoint']).dt.strftime('%H:%M')
    df.drop('timepoint', axis=1, inplace=True)

    return df


def _process_metadata(df, sensor_metadata, station_metadata):
    sensor_units = _get_sensor_units(df, sensor_metadata)
    pc_wetterstation_sensor_ids = _get_pc_wetterstation_sensor_ids(df)

    # the rain data is given in mm and therefore no special configuration is required for it
    station_metadata_line = \
        ('#Calibrate=1.000 #Regen0=0mm #Location={} ({}\N{DEGREE SIGN}, {}\N{DEGREE SIGN}) / {}m #Station={} ({})\n'
         .format(station_metadata['location'],
                 station_metadata['latitude'],
                 station_metadata['longitude'],
                 station_metadata['height'],
                 station_metadata['station_id'],
                 station_metadata['device']))
    sensor_names = _get_sensor_names(df, sensor_metadata)

    return pc_wetterstation_sensor_ids, sensor_names, sensor_units, station_metadata_line


def _get_sensor_names(df, sensor_metadata):
    sensor_names = []
    for sensor_id in df.columns:
        if sensor_id.startswith('temperature'):
            sensor_details = _get_sensor_details(sensor_id)
            sensor_names.append('{} ({})'.format(sensor_metadata['temperature']['description'], sensor_details))
        elif sensor_id.startswith('humidity'):
            sensor_details = _get_sensor_details(sensor_id)
            sensor_names.append('{} ({})'.format(sensor_metadata['humidity']['description'], sensor_details))
        elif sensor_id.startswith('date'):
            sensor_names.append('Datum')
        elif sensor_id.startswith('time'):
            sensor_names.append('Uhrzeit')
        else:
            sensor_names.append(sensor_metadata[sensor_id]['description'])

    return sensor_names


def _get_sensor_details(sensor_id):
    if 'IN' in sensor_id:
        sensor_details = 'Innen'
    elif 'OUT' in sensor_id:
        sensor_index = sensor_id.split('OUT')[1]
        sensor_details = 'Außensensor {}'.format(sensor_index)
    else:
        sensor_details = ''
    return sensor_details


def _get_pc_wetterstation_sensor_ids(df):
    pc_wetterstation_sensor_ids = []
    curr_temp_sensor_id = PC_WETTERSTATION_TEMP_MAPPING['min']
    curr_humid_sensor_id = PC_WETTERSTATION_HUMID_MAPPING['min']
    for sensor_id in df.columns:
        if sensor_id.startswith('temperature'):
            if curr_temp_sensor_id > PC_WETTERSTATION_TEMP_MAPPING['max']:
                raise ValueError('Too many temperature sensors, this is not compatible with PCWetterstation')
            pc_wetterstation_sensor_ids.append(curr_temp_sensor_id)
            curr_temp_sensor_id += 1
        elif sensor_id.startswith('humidity'):
            if curr_humid_sensor_id > PC_WETTERSTATION_HUMID_MAPPING['max']:
                raise ValueError('Too many humidity sensors, this is not compatible with PCWetterstation')
            pc_wetterstation_sensor_ids.append(curr_humid_sensor_id)
            curr_humid_sensor_id += 1
        elif sensor_id.startswith('date'):
            pc_wetterstation_sensor_ids.append(DATE_DUMMY_SENSOR_ID)
        elif sensor_id.startswith('time'):
            pc_wetterstation_sensor_ids.append(TIME_DUMMY_SENSOR_ID)
        else:
            pc_wetterstation_sensor_ids.append(PC_WETTERSTATION_GENERAL_MAPPING[sensor_id])

    return pc_wetterstation_sensor_ids


def _get_sensor_units(df, sensor_metadata):
    sensor_units = []
    for sensor_id in df.columns:
        if sensor_id.startswith('temperature'):
            sensor_units.append(sensor_metadata['temperature']['unit'])
        elif sensor_id.startswith('humidity'):
            sensor_units.append(sensor_metadata['humidity']['unit'])
        elif sensor_id.startswith('date') or sensor_id.startswith('time'):
            sensor_units.append('')
        else:
            sensor_units.append(sensor_metadata[sensor_id]['unit'])

    return sensor_units
