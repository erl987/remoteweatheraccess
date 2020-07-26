from .models import FullUser
from ..extensions import ma


class FullUserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FullUser
        load_instance = True


# initialize the schemas
full_user_load_schema = FullUserSchema(exclude=('id', ))
full_user_dump_schema = FullUserSchema(exclude=('password', ))
full_many_users_schema = FullUserSchema(many=True, exclude=('password', ))
