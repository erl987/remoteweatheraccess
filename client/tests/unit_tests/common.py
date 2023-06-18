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
import datetime

import pytz

from ..common import USER_NAME, URL, PORT

CONNECT_TIMEOUT_IN_MIN = 0.9
WRITE_TIMEOUT_IN_MIN = 5.0

CONFIG = {
    'station_id': 'TES',
    'backend_url': URL,
    'backend_port': PORT,
    'use_ssl': True,
    'user_name': USER_NAME,
    'relogin_time_in_sec': 50,
    'data_reading': {
        'minute_of_first_read_within_an_hour': 0,
        'read_period_in_minutes': 10
    },
    'ignored_data_fields': ['forecast', 'storm_warning'],
    'sleep_period_in_sec': 0.25,
    'timeouts_in_min': {
        'all_datasets_read': 20,
        'latest_dataset_read': 1,
        'server_connect_timeout': CONNECT_TIMEOUT_IN_MIN,
        'server_write_timeout': WRITE_TIMEOUT_IN_MIN
    }
}

A_LOCAL_TIME_POINT = datetime.datetime(year=2023, month=6, day=11, hour=13, minute=42, second=52,
                                       tzinfo=pytz.timezone('UTC')).astimezone(
    pytz.timezone('Europe/Berlin'))
