from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(engine_options={"use_batch_mode": True})
ma = Marshmallow()
flask_bcrypt = Bcrypt()
jwt = JWTManager()
