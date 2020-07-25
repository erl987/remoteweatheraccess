from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
flask_bcrypt = Bcrypt()
ma = Marshmallow()
jwt = JWTManager()
