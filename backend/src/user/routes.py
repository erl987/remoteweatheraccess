from http import HTTPStatus

import flask_bcrypt
from flask import jsonify, request, current_app, Blueprint, Response
from flask_jwt_extended import create_access_token

from .models import FullUser
from .schemas import full_user_load_schema, full_user_dump_schema, full_many_users_schema
from ..exceptions import APIError
from ..extensions import db, jwt
from ..utils import json_with_rollback_and_raise_exception, access_level_required, Role, \
    with_rollback_and_raise_exception

INVALID_PASSWORD_SALT = flask_bcrypt.generate_password_hash('invalid')

user_blueprint = Blueprint('user', __name__, url_prefix='/api/v1')


@user_blueprint.route('/user', methods=['POST'])
@access_level_required(Role.ADMIN)
@json_with_rollback_and_raise_exception
def add_user():
    new_user = full_user_load_schema.load(request.json)

    existing_user = FullUser.query.filter_by(name=new_user.name).first()
    if not existing_user:
        new_user.save_to_db()
        response = jsonify(full_user_dump_schema.dump(new_user))
        current_app.logger.info('Added new user \'{}\' to the database (role: \'{}\')'.format(new_user.name,
                                                                                              new_user.role))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('User \'{}\' already in the database'.format(new_user.name),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/user/{}'.format(existing_user.id))

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

    existing_user = FullUser.query.get(user_id)
    if not existing_user:
        raise APIError('No user with id \'{}\''.format(user_id), status_code=HTTPStatus.NOT_FOUND)

    if updated_user.name != existing_user.name:
        raise APIError('The user name \'{}\' stored for id \'{}\' does not match the name \'{}\' of the submitted '
                       'user'.format(existing_user.name, user_id, updated_user.name),
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/user/{}'.format(existing_user.id))

    existing_user.password = updated_user.password
    existing_user.role = updated_user.role
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
    existing_user = FullUser.query.get(user_id)
    if not existing_user:
        current_app.logger.info('No user with id \'{}\' '.format(user_id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_user)
    db.session.commit()
    current_app.logger.info('Deleted user \'{}\' from the database'.format(existing_user.name))

    response = Response('')
    response.status_code = HTTPStatus.NO_CONTENT
    response.headers['location'] = '/api/v1/user/{}'.format(existing_user.id)

    return response


@user_blueprint.route('/user/<user_id>', methods=['GET'])
@access_level_required(Role.ADMIN)
@with_rollback_and_raise_exception
def get_user_details(user_id):
    user = FullUser.query.get(user_id)
    if not user:
        raise APIError('No user with id \'{}\''.format(user_id), status_code=HTTPStatus.BAD_REQUEST)

    response = jsonify(full_user_dump_schema.dump(user))
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for user \'{}\''.format(user.name))

    return response


@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {'role': user['role']}


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user['name']


@user_blueprint.route('/login', methods=['POST'])
@json_with_rollback_and_raise_exception
def login():
    submitted_user = full_user_load_schema.load(request.json)
    submitted_user.validate_password()
    user_from_db = FullUser.query.filter_by(name=submitted_user.name).first()

    access_token = None
    if user_from_db:
        if flask_bcrypt.check_password_hash(user_from_db.password, submitted_user.password):
            access_token = create_access_token(identity={'name': user_from_db.name, 'role': user_from_db.role},
                                               fresh=True)
    else:
        flask_bcrypt.check_password_hash(INVALID_PASSWORD_SALT, 'something')  # to give always the same runtime

    if access_token:
        current_app.logger.info('User \'{}\' logged in successfully with the password'.format(user_from_db.name))
        return jsonify({'user': user_from_db.name, 'token': access_token}), HTTPStatus.OK
    else:
        raise APIError('User \'{}\' not existing or password incorrect'.format(submitted_user.name),
                       status_code=HTTPStatus.UNAUTHORIZED)
