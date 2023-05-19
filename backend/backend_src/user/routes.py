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

from http import HTTPStatus

import flask_bcrypt
from flask import jsonify, request, current_app, Blueprint, Response
from flask_jwt_extended import create_access_token

from .schemas import full_user_claims_dump_schema, full_user_login_schema
from .schemas import full_user_load_schema, full_user_dump_schema, full_many_users_schema
from ..exceptions import APIError
from ..extensions import db, jwt
from ..models import FullUser, WeatherStation
from ..utils import json_with_rollback_and_raise_exception, access_level_required, Role, convert_to_int
from ..utils import with_rollback_and_raise_exception

INVALID_PASSWORD_SALT = flask_bcrypt.generate_password_hash('invalid')

user_blueprint = Blueprint('user', __name__, url_prefix='/api/v1')


@user_blueprint.route('/user', methods=['POST'])
@access_level_required(Role.ADMIN)
@json_with_rollback_and_raise_exception
def add_user():
    new_user = full_user_load_schema.load(request.json)

    existing_user = FullUser.query.filter_by(name=new_user.name).one_or_none()
    if not existing_user:
        weather_station = WeatherStation.query.filter_by(station_id=new_user.station_id).one_or_none()
        if weather_station:
            new_user.save_to_db()
            response = jsonify(full_user_dump_schema.dump(new_user))
            current_app.logger.info('Added new user \'{}\' to the database (role: \'{}\')'.format(new_user.name,
                                                                                                  new_user.role))
            response.status_code = HTTPStatus.CREATED
        else:
            raise APIError('Provided station id is not existing', status_code=HTTPStatus.BAD_REQUEST)
    else:
        raise APIError('User already in the database', status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/user/{}'.format(existing_user.id))

    response.headers['location'] = '/api/v1/user/{}'.format(new_user.id)

    return response


@user_blueprint.route('/user', methods=['GET'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def get_all_users():
    all_users = FullUser.query.all()
    response = jsonify(full_many_users_schema.dump(all_users))
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for all {} users'.format(len(all_users)))

    return response


@user_blueprint.route('/user/<user_id>', methods=['PUT'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def update_user(user_id):
    updated_user = full_user_load_schema.load(request.json)

    existing_user = FullUser.query.get(convert_to_int(user_id))
    if not existing_user:
        raise APIError('No user with provided id', status_code=HTTPStatus.NOT_FOUND)

    if updated_user.name != existing_user.name:
        raise APIError('The user name stored for the provided id does not match the name of the submitted user',
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/user/{}'.format(existing_user.id))

    weather_station = WeatherStation.query.filter_by(station_id=updated_user.station_id).one_or_none()
    if not weather_station:
        raise APIError('Provided station id is not existing', status_code=HTTPStatus.BAD_REQUEST)

    existing_user.password = updated_user.password
    existing_user.role = updated_user.role
    existing_user.station_id = updated_user.station_id
    existing_user.save_to_db(do_add=False)
    current_app.logger.info('Updated user \'{}\' in the database (new role: \'{}\', new password)'
                            .format(existing_user.name, updated_user.role))

    response = Response('')
    response.status_code = HTTPStatus.NO_CONTENT
    response.headers['location'] = '/api/v1/user/{}'.format(existing_user.id)

    return response


@user_blueprint.route('/user/<user_id>', methods=['DELETE'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def remove_user(user_id):
    existing_user = FullUser.query.get(convert_to_int(user_id, HTTPStatus.NO_CONTENT))
    if not existing_user:
        current_app.logger.info('No user with provided id')
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_user)
    db.session.commit()
    current_app.logger.info('Deleted user \'{}\' from the database'.format(existing_user.name))

    return '', HTTPStatus.NO_CONTENT


@user_blueprint.route('/user/<user_id>', methods=['GET'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def get_user_details(user_id):
    user = FullUser.query.get(convert_to_int(user_id))
    if not user:
        raise APIError('No user with provided id', status_code=HTTPStatus.BAD_REQUEST)

    response = jsonify(full_user_dump_schema.dump(user))
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for user \'{}\''.format(user.name))

    return response


@jwt.additional_claims_loader
def add_claims_to_access_token(user):
    return {'role': user['role']}


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user['name']


@user_blueprint.route('/login', methods=['POST'])
@json_with_rollback_and_raise_exception
def login():
    submitted_user = full_user_login_schema.load(request.json)
    submitted_user.validate_password()
    user_from_db = FullUser.query.filter_by(name=submitted_user.name).one_or_none()

    access_token = None
    if user_from_db:
        if flask_bcrypt.check_password_hash(user_from_db.password, submitted_user.password):
            full_user_claims = full_user_claims_dump_schema.dump(user_from_db)
            identity_claim = {'name': user_from_db.name, 'role': full_user_claims['role']}
            additional_claims = {'station_id': full_user_claims['station_id']}
            access_token = create_access_token(identity=identity_claim,
                                               additional_claims=additional_claims,
                                               fresh=True)
    else:
        flask_bcrypt.check_password_hash(INVALID_PASSWORD_SALT, 'something')  # to give always the same runtime

    if access_token:
        current_app.logger.info('User \'{}\' logged in successfully with the password'.format(user_from_db.name))
        return jsonify({'user': user_from_db.name, 'token': access_token}), HTTPStatus.OK
    else:
        raise APIError('User not existing or password incorrect', status_code=HTTPStatus.UNAUTHORIZED)
