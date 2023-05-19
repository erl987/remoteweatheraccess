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
import datetime
from unittest.mock import Mock, patch

from export_src.utils import get_default_month


class BucketItemMock(object):
    def __init__(self, name):
        self.name = name


def test_get_default_month():
    date_mock = Mock(wraps=datetime.date)
    date_mock.today.return_value = datetime.datetime(1999, 1, 5)
    with patch('datetime.date', new=date_mock):
        default_month = get_default_month()
    assert default_month == (1, 1999)


def test_get_default_month_when_first_day():
    date_mock = Mock(wraps=datetime.date)
    date_mock.today.return_value = datetime.datetime(1999, 1, 1)
    with patch('datetime.date', new=date_mock):
        default_month = get_default_month()
    assert default_month == (12, 1998)
