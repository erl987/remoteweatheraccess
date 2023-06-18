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
USER_NAME = 'a_user'
PASSWORD = 'a_passwd'
TOKEN = 'a_token'

LOGIN_RESPONSE = {
    'token': TOKEN,
    'user': USER_NAME
}

URL = 'something'
PORT = 443

DATA_DIR = 'data_dir'

EXPECTED_DATA_FOR_SINGLE_TIMEPOINT = {
    'station_id': 'TES',
    'pressure': 1018.0,
    'uv': None,
    'rain_counter': 3620,
    'speed': None,
    'gusts': None,
    'direction': None,
    'wind_temperature': None,
    'temperature_humidity': [
        {'sensor_id': 'OUT1', 'temperature': 3.7, 'humidity': 54.0},
        {'sensor_id': 'IN', 'temperature': 22.75, 'humidity': 26.0}
    ]
}
