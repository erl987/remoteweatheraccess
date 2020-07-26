from datetime import datetime
from logging.config import dictConfig

from flask import Flask
from flask.json import JSONEncoder

from src.temp_humidity_sensor.routes import temp_humidity_sensor_blueprint
from src.user.models import generate_default_admin_user, FullUser, DEFAULT_ADMIN_USER_NAME
from src.user.routes import user_blueprint
from src.weatherdata.models import generate_temp_humidity_sensors, TempHumiditySensor, WeatherStation, \
    generate_default_weather_stations
from src.weatherdata.routes import weatherdata_blueprint
from src.errorhandlers import handle_invalid_usage, unauthorized_response
from src.exceptions import APIError
from src.extensions import db, ma, flask_bcrypt, jwt
from config.settings import ProdConfig, DevConfig, Config, LOGGING_CONFIG


class MyJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)


class IsoDateTimeFlask(Flask):
    json_encoder = MyJSONEncoder


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
    app.register_blueprint(temp_humidity_sensor_blueprint)


def register_errorhandlers(app):
    app.errorhandler(APIError)(handle_invalid_usage)
    jwt.unauthorized_loader(unauthorized_response)


def _create_default_admin_user():
    admin_user = generate_default_admin_user()
    admin_password = admin_user.password
    admin_user.save_to_db()
    app.logger.warning('Added a new default ADMIN user \'{}\' with password \'{}\' to the database. '
                       'Create an own admin user with another password and delete the default '
                       'admin user immediately!'.format(admin_user.name, admin_password))


def _create_temp_humidity_sensors():
    sensors = generate_temp_humidity_sensors()
    db.session.add_all(sensors)
    db.session.commit()


def _create_default_weather_stations():
    weather_stations = generate_default_weather_stations()
    db.session.add_all(weather_stations)
    db.session.commit()


# will only be executed if running directly with Python
if __name__ == '__main__':
    app = create_app(DevConfig())
    with app.app_context():
        db.create_all()

        default_admin_user = db.session.query(FullUser).filter(FullUser.name == DEFAULT_ADMIN_USER_NAME).one_or_none()
        if not default_admin_user:
            _create_default_admin_user()

        num_temp_humidity_sensors = db.session.query(TempHumiditySensor).count()
        if num_temp_humidity_sensors == 0:
            _create_temp_humidity_sensors()

        num_stations = db.session.query(WeatherStation).count()
        if num_stations == 0:
            _create_default_weather_stations()

    app.run(host='0.0.0.0', port=8050)
