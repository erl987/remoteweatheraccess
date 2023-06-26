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

from .layout import get_calendar_for_year
from .storage import get_available_data, get_file_contents, get_zip_file_content
from .utils import get_station_id, get_station_label_info_from_backend

logger = logging.getLogger('django')


def download_data_callback(chosen_months_in_year, station_label, year, data_cache, bucket):
    try:
        file_contents, station_id = get_file_contents(chosen_months_in_year, station_label, year, data_cache, bucket)

        if len(file_contents) == 0:
            return None, True, False
        if len(file_contents) == 1:
            csv_file_content = list(file_contents.values())[0].decode('utf-8')
            csv_file_name = list(file_contents.keys())[0]

            return dict(content=csv_file_content, filename=csv_file_name, type='text/csv'), False, False
        else:
            zip_file_content = get_zip_file_content(file_contents)
            zip_file_name = f'weather-data-{station_id}-{year}.zip'

            return (dict(base64=True, content=zip_file_content, filename=zip_file_name, type='application/zip'), False,
                    False)
    except Exception as e:
        logger.error(f'Error in download function: {e}')
        return None, False, True


def update_downloadable_data_callback(station_label, year, data_cache, bucket):
    try:
        station_id = get_station_id(station_label, get_station_label_info_from_backend())
        available_data = get_available_data(data_cache, bucket)
        return get_calendar_for_year(available_data, station_id, year), False
    except Exception as e:
        logger.error(f'Error while updating downloadable data: {e}')
        return None, True
