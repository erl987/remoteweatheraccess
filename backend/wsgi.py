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

"""
Gunicorn application object

Run in the most simple way with:
```
cd backend
export JWT_SECRET_KEY=SECRET-KEY
export DB_PASSWORD=passwd
gunicorn -b :8000 wsgi:app
```
"""

from psycogreen.gevent import patch_psycopg
patch_psycopg()  # needs to be imported as early as possible

import os
from backend_app import create_app
from backend_src.models import prepare_database

app = create_app()

if 'DOCKER_COMPOSE_APP' in os.environ or 'RUNNING_ON_SERVER' in os.environ:
    prepare_database(app)
