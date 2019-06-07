from sqlalchemy.orm import validates

from ..extensions import db
from ..utils import ROLES


class FullUser(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)

    @validates('role')
    def validate_role(self, key, value):
        assert value.upper() in ROLES
        return value

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
