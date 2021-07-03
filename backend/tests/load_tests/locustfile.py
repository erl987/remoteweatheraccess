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

import json
from locust import HttpUser, task, constant


class WebsiteUser(HttpUser):
    wait_time = constant(1.0)

    @task
    def get(self):
        payload = {
            'first_timepoint': '2017-03-11T00:00:00+02:00',
            'last_timepoint': '2019-03-18T00:00:00+02:00',
            'sensors': []
        }
        headers = {
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'}
        self.client.get('/api/v1/data', data=json.dumps(payload), headers=headers)
