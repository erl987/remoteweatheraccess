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

import re
from enum import Enum
from functools import wraps
from http import HTTPStatus

from flask import current_app, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest

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
        if not request.is_json:
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
        raise APIError('Schema validation failed: {}'.format(str(e).split('\n')[0]),
                       status_code=HTTPStatus.BAD_REQUEST)
    except IntegrityError as e:
        # this is specific for psycopg2
        raise APIError(e.orig.diag.message_detail, status_code=HTTPStatus.CONFLICT)
    except BadRequest as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)
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
                    raise APIError('Denied authorization of user for access level \'{}\''.format(required_role.name),
                                   status_code=HTTPStatus.FORBIDDEN)
            except Exception as e:
                raise_api_error(e, HTTPStatus.FORBIDDEN)

        return wrapper

    return decorator


def _verify_and_read_jwt():
    try:
        verify_jwt_in_request()
    except Exception as e:
        raise_api_error(e, status_code=HTTPStatus.UNAUTHORIZED)

    user_name = get_jwt_identity()
    claims = get_jwt()
    user_role = claims['role']
    user_role_id = Role[user_role].value
    approved_station_id = claims['station_id']

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


def validate_items(requested_items, all_items, item_type):
    for item in requested_items:
        if item not in all_items:
            raise APIError('A provided {} is not existing'.format(item_type), status_code=HTTPStatus.BAD_REQUEST)


def convert_to_int(user_id, error_status=HTTPStatus.BAD_REQUEST):
    try:
        user_id = int(user_id)
    except ValueError:
        raise APIError('Invalid id', error_status)
    return user_id
