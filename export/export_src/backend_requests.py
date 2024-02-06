#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
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
import logging
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

logger = logging.getLogger('exporter')


def get_sensor_metadata(url, port):
    r = requests.get('https://{}:{}/api/v1/sensor'.format(url, port))
    r.raise_for_status()
    return reformat_sensor_metadata(r.json())


def reformat_sensor_metadata(metadata_json):
    sensor_metadata = {}
    for row in metadata_json:
        sensor_metadata[row['sensor_id']] = {'description': row['description'], 'unit': row['unit']}

    return sensor_metadata


def get_station_metadata_for(url, port, station_id=None):
    r = requests.get('https://{}:{}/api/v1/station'.format(url, port))
    r.raise_for_status()

    return reformat_station_metadata(r.json(), station_id)


def reformat_station_metadata(metadata_json, station_id):
    if not station_id:
        return metadata_json

    for row in metadata_json:
        if row['station_id'] == station_id:
            return [row]

    raise ValueError('Station {} is not available on the backend'.format(station_id))


def get_weather_data_for(month, year, station_id, url, port):
    first_timepoint = datetime(day=1, month=month, year=year)
    last_timepoint = first_timepoint + relativedelta(months=1)

    logger.info('Requesting data from backend {}:{} for station {}'.format(url, port, station_id))
    r = requests.get('https://{}:{}/api/v1/data?first_timepoint={}&last_timepoint={}&stations={}'.format(
        url,
        port,
        first_timepoint,
        last_timepoint,
        station_id
    ))
    logger.info('Received data for period {} - {}'.format(first_timepoint, last_timepoint))
    r.raise_for_status()
    month_data = r.json()
    return month_data
