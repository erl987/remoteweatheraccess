from datetime import datetime
from logging.config import dictConfig

from flask import Flask
from flask.json import JSONEncoder

from restapi_backend.src.user.models import DefaultAdminCreationStatus, generate_default_admin_user
from src.user.routes import user_blueprint
from src.weatherdata.routes import weatherdata_blueprint
from src.errorhandlers import handle_invalid_usage, unauthorized_response
from src.exceptions import APIError
from src.extensions import db, flask_bcrypt, jwt
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
    flask_bcrypt.init_app(app)
    jwt.init_app(app)


def register_blueprints(app):
    app.register_blueprint(user_blueprint)
    app.register_blueprint(weatherdata_blueprint)


def register_errorhandlers(app):
    app.errorhandler(APIError)(handle_invalid_usage)
    jwt.unauthorized_loader(unauthorized_response)


# will only be executed if running directly with Python
if __name__ == '__main__':
    app = create_app(DevConfig())
    with app.app_context():
        db.create_all()

        default_admin_query_result = DefaultAdminCreationStatus.query.first()
        was_default_admin_already_created = False
        if default_admin_query_result and default_admin_query_result.isDefaultAdminCreated:
            was_default_admin_already_created = True

        if not was_default_admin_already_created:
            # this user is only intended for the first usage and needs to be deleted by the user!
            default_admin_creation_status = DefaultAdminCreationStatus()
            default_admin_creation_status.isDefaultAdminCreated = True
            db.session.add(default_admin_creation_status)
            db.session.commit()

            default_admin_user = generate_default_admin_user()
            admin_password = default_admin_user.password
            default_admin_user.save_to_db()
            app.logger.warning('Added a new default ADMIN user \'{}\' with password \'{}\' to the database. '
                               'Create an own admin user with another password and delete the default '
                               'admin user immediately!'.format(default_admin_user.name, admin_password))

    app.run(host='0.0.0.0', port=8050)
