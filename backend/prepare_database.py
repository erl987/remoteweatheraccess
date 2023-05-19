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
Helper application to set up the database in the production environment so that the backend application can run

Run in the most simple way with:
```
cd backend
export DB_URL=database url
export DB_USER_DB_USER=userdb
export DB_USER_DB_PASSWORD=password
export DB_WEATHER_DB_USER=weatherdatadb
export DB_WEATHER_DB_PASSWORD=password
export DB_USER_DATABASE=users
export DB_WEATHER_DATABASE=weatherdata
python3 prepare_database.py
```
"""

from backend_app import create_app
from backend_config.settings import ProdConfig
from backend_src.models import prepare_database

if __name__ == '__main__':
    app = create_app(ProdConfig())
    prepare_database(app)
    app.logger.info('Database successfully prepared for usage by the application')
