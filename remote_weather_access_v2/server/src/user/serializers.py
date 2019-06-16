from http import HTTPStatus

import marshmallow
from flask_marshmallow.sqla import ModelSchema
from marshmallow import pre_load

from .models import FullUser
from ..utils import USER_NAME_REGEX
from ..exceptions import APIError


class FullUserSchema(ModelSchema):
    class Meta:
        strict = True
        model = FullUser


full_user_schema = FullUserSchema()


class UserWithPasswordSchema(marshmallow.Schema):
    name = marshmallow.fields.Str(required=True)
    password = marshmallow.fields.Str(required=True)

    @pre_load
    def validate(self, data, **kwargs):
        if USER_NAME_REGEX.match(data['name']) is None:
            raise APIError('User name does not fulfill the constraints (3-30 characters, only letters, '
                           'digits and "-_.")'.format(id), status_code=HTTPStatus.BAD_REQUEST)
        if len(data['password']) < 3 or len(data['password']) > 30:
            raise APIError('Password does not fulfill constraints (3-30 characters)',
                           status_code=HTTPStatus.BAD_REQUEST)

        return data


user_with_password_schema = UserWithPasswordSchema(strict=True)


def deserialize_full_user(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    user = full_user_schema.load(json)
    return user.data


def deserialize_user_with_password(json):
    if not json:
        raise APIError('Required Content-Type is `application/json`', status_code=HTTPStatus.BAD_REQUEST)

    user = user_with_password_schema.load(json)
    return user.data
