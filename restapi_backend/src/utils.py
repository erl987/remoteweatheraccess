import random
import string
import re
from enum import Enum
from functools import wraps
from http import HTTPStatus

import pytz
from dataclasses_jsonschema import ValidationError
from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_jwt_identity

from .extensions import db
from .exceptions import raise_api_error, APIError


class Role(Enum):
    PULL_USER = 0
    PUSH_USER = 1
    ADMIN = 2


ROLES = set(item.name for item in Role)


USER_NAME_REGEX = re.compile(r'^(?![-._])(?!.*[_.-]{2})[\w.-]{3,30}(?<![-._])$')


def json_with_rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        json = request.json
        if not json:
            raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

        return _perform_with_rollback_and_raise_exception(func, args, kwds)

    return wrapper


def with_rollback_and_raise_exception(func):
    @wraps(func)
    def wrapper(*args, **kwds):
        return _perform_with_rollback_and_raise_exception(func, args, kwds)

    return wrapper


def _perform_with_rollback_and_raise_exception(func, args, kwds):
    try:
        return func(*args, **kwds)
    except ValidationError as e:
        raise APIError("Schema validation failed: {}".format(str(e).split("\n")[0]),
                       status_code=HTTPStatus.BAD_REQUEST)
    except Exception as e:
        db.session.rollback()
        raise raise_api_error(e, status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        db.session.close()


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
