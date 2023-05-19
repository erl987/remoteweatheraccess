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

from datetime import datetime
from logging.config import dictConfig

from flask import Flask
from flask.json import JSONEncoder

from backend_config.settings import ProdConfig, DevConfig, Config, LOGGING_CONFIG
from backend_src.errorhandlers import handle_invalid_usage, unauthorized_response
from backend_src.exceptions import APIError
from backend_src.extensions import db, ma, flask_bcrypt, jwt
from backend_src.models import prepare_database
from backend_src.sensor.routes import sensor_blueprint
from backend_src.station.routes import station_blueprint
from backend_src.temp_humidity_sensor.routes import temp_humidity_sensor_blueprint
from backend_src.user.routes import user_blueprint
from backend_src.weatherdata.routes import weatherdata_blueprint


class IsoDateTimeJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class IsoDateTimeFlask(Flask):
    json_encoder = IsoDateTimeJSONEncoder


def create_app(config_object: Config = ProdConfig()):
    app = IsoDateTimeFlask(__name__)

    dictConfig(LOGGING_CONFIG)
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)

    return app


def register_extensions(app):
    db.init_app(app)
    ma.init_app(app)
    flask_bcrypt.init_app(app)
    jwt.init_app(app)


def register_blueprints(app):
    app.register_blueprint(user_blueprint)
    app.register_blueprint(weatherdata_blueprint)
    app.register_blueprint(sensor_blueprint)
    app.register_blueprint(temp_humidity_sensor_blueprint)
    app.register_blueprint(station_blueprint)


def register_errorhandlers(app):
    app.errorhandler(APIError)(handle_invalid_usage)
    jwt.unauthorized_loader(unauthorized_response)


def main():
    app = create_app(DevConfig())
    prepare_database(app)

    app.run(host='0.0.0.0', port=8000)


# will only be executed if running directly with Python
if __name__ == '__main__':
    main()
