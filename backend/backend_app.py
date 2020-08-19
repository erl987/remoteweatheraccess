from datetime import datetime
from logging.config import dictConfig

from psycogreen.gevent import patch_psycopg

from src.models import prepare_database

patch_psycopg()  # needs to be imported as early as possible

from flask import Flask
from flask.json import JSONEncoder

from src.sensor.routes import sensor_blueprint
from src.station.routes import station_blueprint
from src.temp_humidity_sensor.routes import temp_humidity_sensor_blueprint
from src.user.routes import user_blueprint
from src.weatherdata.routes import weatherdata_blueprint
from src.errorhandlers import handle_invalid_usage, unauthorized_response
from src.exceptions import APIError
from src.extensions import db, ma, flask_bcrypt, jwt
from config.settings import ProdConfig, DevConfig, Config, LOGGING_CONFIG


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
    register_before_first_request(app)
    register_errorhandlers(app)

    return app


def register_before_first_request(app):
    def setup():
        db.create_all()

    app.before_first_request(setup)


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


# will only be executed if running directly with Python
if __name__ == '__main__':
    app = create_app(DevConfig())
    prepare_database(app)

    app.run(host='0.0.0.0', port=8000)