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

import pytest

from backend_src.utils import calc_dewpoint


def test_calc_dew_point():
    dew_points = calc_dewpoint(temperature=[30.5, -5.2], humidity=[74.2, 23.1])
    assert len(dew_points) == 2
    assert dew_points[0] == 25.4
    assert dew_points[1] == -21.3


def test_calc_dew_point_on_limits():
    dew_points = calc_dewpoint(temperature=[0, 0], humidity=[0, 100])
    assert len(dew_points) == 2
    assert dew_points[0] is None
    assert dew_points[1] == 0


def test_calc_dew_point_if_input_is_none():
    dew_points = calc_dewpoint(temperature=[None, 10, None], humidity=[10, None, None])
    assert len(dew_points) == 3
    assert dew_points[0] is None
    assert dew_points[1] is None
    assert dew_points[2] is None
