#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..models import FullUser
from ..extensions import ma


class FullUserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = FullUser
        include_fk = True
        load_instance = True


# initialize the schemas
full_user_load_schema = FullUserSchema(exclude=('id', ))
full_user_login_schema = FullUserSchema(exclude=('id', 'role', 'station_id'))
full_user_dump_schema = FullUserSchema(exclude=('password', ))
full_many_users_schema = FullUserSchema(many=True, exclude=('password', ))
full_user_claims_dump_schema = FullUserSchema(exclude=('name', 'id', 'password'))
