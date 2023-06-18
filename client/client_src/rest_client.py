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
import gzip
import json
import logging
import os
import time
from datetime import datetime
from io import BytesIO

import requests

from .utils import IsoDateTimeJSONEncoder


class ServerProxy(object):
    def __init__(self, config):
        self.url = config['backend_url']
        self.port = config['backend_port']
        self._user_name = config['user_name']
        if not config['use_ssl']:
            self._protocol = 'http'
        else:
            self._protocol = 'https'
        self._relogin_time_in_sec = config['relogin_time_in_sec']

        if 'BACKEND_PASSWORD' not in os.environ:
            raise ValueError('The backend API password for the user defined in the config file must be provided '
                             'in the environment variable \'BACKEND_PASSWORD\'')
        self._password = os.environ['BACKEND_PASSWORD']

        self._server_connect_timeout_in_s = 60 * config['timeouts_in_min']['server_connect_timeout']
        self._server_write_timeout_in_s = 60 * config['timeouts_in_min']['server_write_timeout']

        self._token = None
        self._last_login_time = datetime.min

    def send_data(self, json_data, station_id: str):
        logging.debug(f'Sending read data to server {self.url}:{self.port}')
        first_date, last_date = self._get_first_and_last_date(json_data)

        if len(json_data) > 0:
            jwt_token = self._perform_login()
            zipped_json = self._zip_payload(json_data)
            start_time = time.time()
            r = requests.post('{}://{}:{}/api/v1/data'.format(self._protocol, self.url, self.port),
                              data=zipped_json,
                              headers=self._get_headers(jwt_token),
                              timeout=self._get_timeouts())
            end_time = time.time()
            r.raise_for_status()
            logging.debug(f'Upload for station {station_id} in time period {first_date} - {last_date} '
                          f'took {(end_time - start_time) * 1000} ms, status code {r.status_code}')

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
            logging.debug('Logging into the backend')
            r = requests.post('{}://{}:{}/api/v1/login'.format(self._protocol, self.url, self.port),
                              json={'name': self._user_name, 'password': self._password},
                              headers=self._get_headers(),
                              timeout=self._get_timeouts())
            r.raise_for_status()
            self._token = r.json()['token']
            self._last_login_time = datetime.utcnow()
            return self._token
        else:
            return self._token

    def _get_timeouts(self):
        return self._server_connect_timeout_in_s, self._server_write_timeout_in_s
