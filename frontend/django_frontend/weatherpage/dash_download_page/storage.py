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

from base64 import b64encode
from datetime import datetime
from io import BytesIO
from logging import getLogger
from os import environ

from stream_zip import ZIP_32, stream_zip

from .utils import is_deployed_environment, get_station_label_info_from_backend, get_station_id

logger = getLogger('django')


def get_available_data(data_cache, bucket):
    data = data_cache.get('available-data')
    if not data:
        if not is_deployed_environment() and 'TEST_WITH_BUCKET_MOCK' not in environ:
            return {}

        logger.info('Obtaining list of data blobs')
        blobs = bucket.list_blobs()

        data = {}
        for blob in blobs:
            if 'EXP' not in blob.name:
                continue

            month, station_id, year = _extract_metadata(blob)

            if station_id not in data:
                data[station_id] = {}
            if year not in data[station_id]:
                data[station_id][year] = []

            data[station_id][year].append((month, blob.name))

        data_cache.set('available-data', data)

    return data


def _download_file_content(file_blob_name, bucket):
    logger.info(f'Downloading blob {file_blob_name}')

    file_obj = BytesIO()

    blob = bucket.blob(file_blob_name)
    blob.download_to_file(file_obj)

    return file_obj.getvalue()


def _get_data_blob_names(months_in_year, station_id, year, data_cache, bucket):
    data_for_year = get_available_data(data_cache, bucket)[station_id][year]

    data_files = []
    for month in months_in_year:
        for item in data_for_year:
            if item[0] == month:
                data_files.append(item[1])
                break

    if len(data_files) != len(months_in_year):
        raise AssertionError('Months in year does not match the available data')

    return data_files


def _get_months_in_year(chosen_months_in_year):
    months_in_year = []

    if len(chosen_months_in_year) > 0:
        for month in range(1, 12 + 1):
            if chosen_months_in_year[month - 1]:
                months_in_year.append(month)

    return months_in_year


def _zip_member_files(file_contents):
    modified_at = datetime.now()
    perms = 0o600

    for file_name, binary_content in file_contents.items():
        yield file_name, modified_at, perms, ZIP_32, (binary_content,)


def get_file_contents(chosen_months_in_year, station_label, year, data_cache, bucket):
    station_id = get_station_id(station_label, get_station_label_info_from_backend())
    months_in_year = _get_months_in_year(chosen_months_in_year)
    data_blob_names = _get_data_blob_names(months_in_year, station_id, year, data_cache, bucket)

    file_contents = {}
    for blob_name in data_blob_names:
        file_name = blob_name.split('/')[1]
        file_contents[file_name] = _download_file_content(blob_name, bucket)

    return file_contents, station_id


def get_zip_file_content(file_contents):
    logger.info('Creating ZIP file for content')

    zipped_chunks = stream_zip(_zip_member_files(file_contents))

    zip_stream = BytesIO()
    for chunk in zipped_chunks:
        zip_stream.write(chunk)

    return b64encode(zip_stream.getvalue()).decode('ascii')


def _extract_metadata(blob):
    station_id, file_name = blob.name.split('/')
    file_name = file_name.replace('EXP', '')

    month_str, year_str = file_name.split('_')
    year_str = year_str.split('.')[0]

    month = int(month_str)
    year = 2000 + int(year_str)

    return month, station_id, year
