import random
import string
from enum import Enum
from functools import wraps
from http import HTTPStatus

import pytz
from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_jwt_identity

from .extensions import db
from .exceptions import raise_api_error, APIError


class Role(Enum):
    PULL_USER = 0
    PUSH_USER = 1
    ADMIN = 2


ROLES = set(item.name for item in Role)


def to_utc(dt):
    if dt.tzinfo:
        timepoint = dt.astimezone(pytz.utc)
    else:
        timepoint = dt
    timepoint = timepoint.replace(tzinfo=None)

    return timepoint


def rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception as e:
            db.session.rollback()
            raise raise_api_error(e, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            db.session.close()
    return wrapper


def access_level_required(required_role: Role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            user_role = get_jwt_claims()['role']
            user_role_id = Role[user_role].value
            if user_role_id == required_role.value:
                current_app.logger.info('Approved authorization of user \'{}\' for access level \'{}\''.format(
                    get_jwt_identity(), required_role.name))
                return fn(*args, **kwargs)
            else:
                raise APIError('Denied authorization of user \'{}\' for access level \'{}\''
                               .format(get_jwt_identity(), required_role.name), status_code=HTTPStatus.FORBIDDEN)

        return wrapper
    return decorator


def generate_random_password(string_length=8):
    password_characters = string.ascii_letters + string.digits
    return ''.join(random.choice(password_characters) for i in range(string_length))
