from dataclasses import dataclass
from http import HTTPStatus

from sqlalchemy.orm import validates

from ..exceptions import APIError
from ..extensions import db, flask_bcrypt
from ..utils import ROLES, Role, generate_random_password, USER_NAME_REGEX


DEFAULT_ADMIN_USER_NAME = 'default_admin'


@dataclass
class FullUser(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)

    name: str = db.Column(db.String(120), unique=True, nullable=False)
    password: str = db.Column(db.String(120), nullable=False)
    role: str = db.Column(db.String(10), nullable=False)

    @validates('role')
    def validate_role(self, key, value):
        if value.upper() not in ROLES:
            raise APIError('Role not existing', status_code=HTTPStatus.BAD_REQUEST)
        return value

    @validates('name')
    def validate_name(self, key, value):
        if USER_NAME_REGEX.match(value) is None:
            raise APIError('User name does not fulfill the constraints (3-30 characters, only letters, '
                           'digits and "-_.")'.format(id), status_code=HTTPStatus.BAD_REQUEST)
        return value

    def validate_password(self):
        if not self.password or len(self.password) < 3 or len(self.password) > 30:
            raise APIError('Password does not fulfill constraints (3-30 characters)',
                           status_code=HTTPStatus.BAD_REQUEST)

    def save_to_db(self, do_add=True):
        self.validate_password()
        self.password = flask_bcrypt.generate_password_hash(self.password)
        self.role = self.role.upper()
        if do_add:
            db.session.add(self)
        db.session.commit()


def generate_default_admin_user():
    default_admin = FullUser()
    default_admin.name = DEFAULT_ADMIN_USER_NAME
    default_admin.password = generate_random_password()
    default_admin.role = Role.ADMIN.name

    return default_admin
