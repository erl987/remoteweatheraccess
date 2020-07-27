import random
import re
import string
from enum import Enum
from functools import wraps
from http import HTTPStatus
from sqlite3 import Connection as SQLite3Connection

from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from .exceptions import raise_api_error, APIError
from .extensions import db


class Role(Enum):
    GUEST = 0
    PULL_USER = 1  # currently not used
    PUSH_USER = 2
    ADMIN = 3


ROLES = set(item.name for item in Role)

USER_NAME_REGEX = re.compile(r'^(?![-._])(?!.*[_.-]{2})[\w.-]{3,30}(?<![-._])$')


def json_with_rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        json = request.json
        if not json:
            raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

        return _perform_with_rollback_and_raise_exception(func, args, kwargs)

    return wrapper


def with_rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _perform_with_rollback_and_raise_exception(func, args, kwargs)

    return wrapper


def _perform_with_rollback_and_raise_exception(func, args, kwargs):
    try:
        return func(*args, **kwargs)
    except ValidationError as e:
        raise APIError('Schema validation failed: {}'.format(str(e).split("\n")[0]),
                       status_code=HTTPStatus.BAD_REQUEST)
    except IntegrityError as e:
        if 'FOREIGN KEY constraint failed' in str(e):
            raise APIError('One of the keys contained in the submitted request (like temp_humidity_sensor or station '
                           'id) does not exist on the server', status_code=HTTPStatus.BAD_REQUEST)
        else:
            raise_api_error(e, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        db.session.rollback()
        db.session.close()


def access_level_required(required_role: Role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                is_approved = False

                if required_role == Role.GUEST:
                    user_name = 'guest'
                    is_approved = True
                else:
                    user_name, user_role_id, __ = _verify_and_read_jwt()

                    if user_role_id == Role.ADMIN.value:
                        is_approved = True

                    if user_role_id == required_role.value:
                        is_approved = True

                if is_approved:
                    current_app.logger.info('Approved authorization of user \'{}\' for access level \'{}\''
                                            .format(user_name, required_role.name))
                    return fn(*args, **kwargs)
                else:
                    raise APIError('Denied authorization of user \'{}\' for access level \'{}\''
                                   .format(user_name, required_role.name), status_code=HTTPStatus.FORBIDDEN)
            except Exception as e:
                raise_api_error(e, HTTPStatus.FORBIDDEN)

        return wrapper

    return decorator


def generate_random_password(string_length=8):
    password_characters = string.ascii_letters + string.digits
    return ''.join(random.choice(password_characters) for _ in range(string_length))


def _verify_and_read_jwt():
    try:
        verify_jwt_in_request()
    except Exception as e:
        raise_api_error(e, status_code=HTTPStatus.UNAUTHORIZED)

    user_name = get_jwt_identity()
    user_claims = get_jwt_claims()
    user_role = user_claims['role']
    user_role_id = Role[user_role].value
    approved_station_id = user_claims['station_id']

    return user_name, user_role_id, approved_station_id



def approve_committed_station_ids(station_ids_in_commit):
    __, user_role_id, approved_station_id = _verify_and_read_jwt()

    if user_role_id == Role.ADMIN.value:
        return
    elif user_role_id == Role.PUSH_USER.value:
        if not approved_station_id:
            is_approved = False
        else:
            is_approved = True
            for station_id_in_commit in station_ids_in_commit:
                if station_id_in_commit != approved_station_id:
                    is_approved = False
                    break

        if not is_approved:
            raise APIError('The commit contains data for stations that the user has no approval for',
                           status_code=HTTPStatus.FORBIDDEN)


@event.listens_for(Engine, 'connect')
def _set_sqlite_pragma(dbapi_connection, __):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.close()
