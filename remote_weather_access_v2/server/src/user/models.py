from http import HTTPStatus

from sqlalchemy.orm import validates

from ..exceptions import APIError
from ..extensions import db, flask_bcrypt
from ..utils import ROLES, Role, generate_random_password, USER_NAME_REGEX


class FullUser(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)

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

    def save_to_db(self, do_add=True):
        if len(self.password) < 3 or len(self.password) > 30:
            raise APIError('Password does not fulfill constraints (3-30 characters)',
                           status_code=HTTPStatus.BAD_REQUEST)

        self.password = flask_bcrypt.generate_password_hash(self.password)
        self.role = self.role.upper()
        if do_add:
            db.session.add(self)
        db.session.commit()


def generate_default_admin_user():
    default_admin = FullUser()
    default_admin.name = 'admin'
    default_admin.password = generate_random_password()
    default_admin.role = Role.ADMIN.name

    return default_admin


class DefaultAdminCreationStatus(db.Model):
    __tablename__ = 'defaultAdminCreationStatus'

    id = db.Column(db.Integer, primary_key=True)
    isDefaultAdminCreated = db.Column(db.Boolean, unique=True, nullable=False)
