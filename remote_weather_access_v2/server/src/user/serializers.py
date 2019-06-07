from http import HTTPStatus

import marshmallow
from flask_marshmallow.sqla import ModelSchema

from .models import FullUser
from ..exceptions import APIError


class FullUserSchema(ModelSchema):
    class Meta:
        strict = True
        model = FullUser


full_user_schema = FullUserSchema()


class UserWithPasswordSchema(marshmallow.Schema):
    name = marshmallow.fields.Str(required=True)
    password = marshmallow.fields.Str(required=True)


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
