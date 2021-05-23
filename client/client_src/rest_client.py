#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
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
import gzip
import json
import time
from datetime import datetime
from io import BytesIO

import requests

from .utils import IsoDateTimeJSONEncoder


class ServerProxy(object):
    def __init__(self, config):
        self._url = config['backend_url']
        self._port = config['backend_port']
        self._user_name = config['user_name']
        if not config['use_ssl']:
            self._protocol = 'http'
        else:
            self._protocol = 'https'
        self._password = config['password']
        self._local_time_zone = config['time_zone']
        self._relogin_time_in_sec = config['relogin_time_in_sec']

        self._token = None
        self._last_login_time = datetime.min
        self._log_buffer = []

    def send_data(self, json_data, station_id: str):
        first_date, last_date = self._get_first_and_last_date(json_data)

        if len(json_data) > 0:
            jwt_token = self._perform_login()
            zipped_json = self._zip_payload(json_data)
            start_time = time.time()
            r = requests.post('{}://{}:{}/api/v1/data'.format(self._protocol, self._url, self._port),
                              data=zipped_json,
                              headers=self._get_headers(jwt_token))
            end_time = time.time()
            r.raise_for_status()
            self._log_buffer.append(('INFO',
                                     'Upload for station {} in time period {} - {} took {} ms, status code {}'
                                     .format(
                                         station_id,
                                         first_date,
                                         last_date,
                                         (end_time - start_time) * 1000,
                                         r.status_code)))

    @staticmethod
    def _get_first_and_last_date(json_data):
        if len(json_data) > 0:
            first_date = json_data[0]['timepoint']
            last_date = json_data[-1]['timepoint']
        else:
            first_date = None
            last_date = None

        return first_date, last_date

    @staticmethod
    def _get_headers(jwt_token=None):
        headers = {
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json'
        }

        if jwt_token:
            headers['Authorization'] = 'Bearer {}'.format(jwt_token)

        return headers

    @staticmethod
    def _zip_payload(object_payload) -> bytes:
        json_payload = json.dumps(object_payload, cls=IsoDateTimeJSONEncoder)
        byte_stream = BytesIO()
        with gzip.GzipFile(fileobj=byte_stream, mode='w') as g:
            g.write(bytes(json_payload, 'utf8'))

        return byte_stream.getvalue()

    def _perform_login(self):
        if (datetime.utcnow() - self._last_login_time).total_seconds() > self._relogin_time_in_sec:
            self._log_buffer.append(('INFO', 'Logging into the backend'))
            r = requests.post('{}://{}:{}/api/v1/login'.format(self._protocol, self._url, self._port),
                              json={'name': self._user_name, 'password': self._password},
                              headers=self._get_headers())
            r.raise_for_status()
            self._token = r.json()['token']
            self._last_login_time = datetime.utcnow()
            return self._token
        else:
            return self._token