from http import HTTPStatus

import flask_bcrypt
from flask import jsonify, request, current_app, Blueprint
from flask_jwt_extended import create_access_token

from .serializers import deserialize_full_user, deserialize_user_with_password
from .models import FullUser
from ..extensions import db, jwt
from ..exceptions import raise_api_error, APIError
from ..utils import rollback_and_raise_exception, access_level_required, Role

INVALID_PASSWORD_SALT = flask_bcrypt.generate_password_hash('invalid')


user_blueprint = Blueprint('user', __name__, url_prefix='/api/v1')


@user_blueprint.route('/user', methods=['POST'])
@access_level_required(Role.ADMIN)
@rollback_and_raise_exception
def add_user():
    try:
        new_user = deserialize_full_user(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    existing_user = FullUser.query.filter_by(name=new_user.name).first()
    if not existing_user:
        new_user.save_to_db()
        response = jsonify({'name': new_user.name, 'role': new_user.role})
        current_app.logger.info('Added new user \'{}\' to the database (role: \'{}\')'.format(new_user.name,
                                                                                              new_user.role))
        response.status_code = HTTPStatus.CREATED
    else:
        raise APIError('User \'{}\' already in the database'.format(new_user.name),
                       status_code=HTTPStatus.CONFLICT, location='/api/v1/user/{}'.format(existing_user.id))

    response.headers['location'] = '/api/v1/data/{}'.format(new_user.id)

    return response


@user_blueprint.route('/user', methods=['GET'])
@access_level_required(Role.ADMIN)
@rollback_and_raise_exception
def get_all_users():
    all_users = []
    for user in FullUser.query.all():
        all_users.append({"id": user.id, "name": user.name})

    response = jsonify(all_users)
    response.status_code = HTTPStatus.OK
    current_app.logger.info('Provided details for all ({}) users'.format(len(all_users)))

    return response


@user_blueprint.route('/user/<id>', methods=['PUT'])
@access_level_required(Role.ADMIN)
@rollback_and_raise_exception
def update_user(id):
    try:
        new_user = deserialize_full_user(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    existing_user = FullUser.query.get(id)
    if not existing_user:
        raise APIError('No user with id \'{}\''.format(id), status_code=HTTPStatus.NOT_FOUND)

    if new_user.name != existing_user.name:
        raise APIError('The user name \'{}\' stored for id \'{}\' does not match the name \'{}\' of the submitted '
                       'user'.format(existing_user.name, id, new_user.name),
                       status_code=HTTPStatus.CONFLICT,
                       location='/api/v1/data/{}'.format(existing_user.id))

    existing_user.password = new_user.password
    existing_user.role = new_user.role
    existing_user.save_to_db(do_add=False)
    current_app.logger.info('Updated user \'{}\' in the database (role: \'{}\')'.format(existing_user.name,
                                                                                        existing_user.role))

    response = jsonify({'name': existing_user.name, 'role': existing_user.role})
    response.status_code = HTTPStatus.OK
    response.headers['location'] = '/api/v1/data/{}'.format(existing_user.id)

    return response


@user_blueprint.route('/user/<id>', methods=['DELETE'])
@access_level_required(Role.ADMIN)
@rollback_and_raise_exception
def remove_user(id):
    existing_user = FullUser.query.get(id)
    if not existing_user:
        current_app.logger.info('No user with id \'{}\' '.format(id))
        return '', HTTPStatus.NO_CONTENT

    db.session.delete(existing_user)
    db.session.commit()
    current_app.logger.info('Deleted user \'{}\' from the database'.format(existing_user.name))

    response = jsonify({'name': existing_user.name, 'role': existing_user.role})
    response.status_code = HTTPStatus.OK

    return response


@user_blueprint.route('/user/<id>', methods=['GET'])
@access_level_required(Role.ADMIN)
@rollback_and_raise_exception
def get_user_details(id):
    user = FullUser.query.get(id)
    if not user:
        raise APIError('No user with id \'{}\''.format(id), status_code=HTTPStatus.BAD_REQUEST)

    response = jsonify({'name': user.name, 'role': user.role})
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
def login():
    try:
        submitted_user = deserialize_user_with_password(request.json)
    except Exception as e:
        raise raise_api_error(e, status_code=HTTPStatus.BAD_REQUEST)

    user_from_db = FullUser.query.filter_by(name=submitted_user['name']).first()

    access_token = None
    if user_from_db:
        if flask_bcrypt.check_password_hash(user_from_db.password, submitted_user['password']):
            access_token = create_access_token(identity={'name': user_from_db.name, 'role': user_from_db.role},
                                               fresh=True)
    else:
        flask_bcrypt.check_password_hash(INVALID_PASSWORD_SALT, 'something')  # to give always the same runtime

    if access_token:
        current_app.logger.info('User \'{}\' logged in successfully with the password'.format(user_from_db.name))
        return jsonify({'user': user_from_db.name, 'token': access_token}), HTTPStatus.OK
    else:
        raise APIError('User \'{}\' not existing or password incorrect'.format(submitted_user['name']),
                       status_code=HTTPStatus.UNAUTHORIZED)
