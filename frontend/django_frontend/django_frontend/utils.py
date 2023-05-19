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


def trigger_startup_of_backend_service():
    from requests import get
    from os import environ

    api_version = '/api/v1'
    endpoint = 'data/limits'

    try:
        backend_url = environ['BACKEND_URL']
        backend_port = environ['BACKEND_PORT']

        if environ['BACKEND_DO_USE_HTTPS'].lower().strip().startswith('true'):
            scheme = 'https'
        else:
            scheme = 'http'

        r = get('{}://{}:{}{}/{}'.format(scheme,
                                         backend_url,
                                         backend_port,
                                         api_version,
                                         endpoint))
        r.raise_for_status()

        print(f'The backend \'{backend_url}:{backend_port}\' is ready')
    except Exception as e:
        print(f'Error triggering the backend service: {e}')
