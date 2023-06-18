#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2023 Ralf Rettig (info@personalfme.de)
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
import json

from client_src.utils import IsoDateTimeJSONEncoder, IsoDateTimeJSONDecoder
from .common import A_LOCAL_TIME_POINT


def test_encoder():
    json_object = json.dumps({'a_time_point': A_LOCAL_TIME_POINT}, cls=IsoDateTimeJSONEncoder)
    assert json_object == '{"a_time_point": "2023-06-11T15:42:52+02:00"}'


def test_decoder():
    json_str = '{"a_time_point": "2023-06-11T15:42:52+02:00"}'
    json_object = json.loads(json_str, cls=IsoDateTimeJSONDecoder)
    assert json_object['a_time_point'] == A_LOCAL_TIME_POINT
