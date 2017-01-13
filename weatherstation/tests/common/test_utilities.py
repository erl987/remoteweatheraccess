# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2016 Ralf Rettig (info@personalfme.de)
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.If not, see <http://www.gnu.org/licenses/>

import unittest
from datetime import datetime

from weathernetwork.common import utilities
from weathernetwork.server.exceptions import NoContentError


def a_number():
    return 22.9


def a_number_string():
    return "5.7"


def a_normal_string():
    return "some string"


def bracket_content():
    return "content"


def a_bracket_containing_string():
    return "(" + bracket_content() + ") Test"


def times(index):
    available_times = [datetime(year=2017, month=1, day=5, hour=10, minute=5, second=30),
                       datetime(year=2017, month=1, day=6, hour=10, minute=5, second=30),
                       datetime(year=2017, month=1, day=7, hour=23, minute=20, second=5),
                       datetime(year=2017, month=1, day=8, hour=10, minute=5, second=30),
                       datetime(year=2017, month=1, day=9, hour=20, minute=21, second=9)]

    return available_times[index]


class TestUtilities(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_float(self):
        self.assertTrue(utilities.is_float(a_number_string()))

    def test_is_float_not_a_number(self):
        self.assertFalse(utilities.is_float(a_normal_string()))

    def test_floor_to_n(self):
        self.assertEqual(utilities.floor_to_n(a_number(), 5), 20)

    def test_floor_to_n_for_negative_number(self):
        self.assertEqual(utilities.floor_to_n(-a_number(), 5), -25)

    def test_ceil_to_n(self):
        self.assertEqual(utilities.ceil_to_n(a_number(), 5), 25)

    def test_ceil_to_n_for_negative_number(self):
        self.assertEqual(utilities.ceil_to_n(-a_number(), 5), -20)

    def test_consolidate_ranges_merging(self):
        # given:
        range_1 = (times(0), times(2))
        range_2 = (times(1), times(4))

        # when:
        consolidated_range = utilities.consolidate_ranges([range_1, range_2])

        # then:
        self.assertEqual(consolidated_range, [(times(0), times(4))])

    def test_consolidate_ranges_no_merging(self):
        # given:
        range_1 = (times(0), times(2))
        range_2 = (times(3), times(4))

        # when:
        consolidated_range = utilities.consolidate_ranges([range_1, range_2])

        # then:
        self.assertEqual(consolidated_range, [(times(0), times(2)), (times(3), times(4))])

    def test_consolidate_ranges_containing(self):
        # given:
        range_1 = (times(0), times(3))
        range_2 = (times(1), times(2))

        # when:
        consolidated_range = utilities.consolidate_ranges([range_1, range_2])

        # then:
        self.assertEqual(consolidated_range, [(times(0), times(3))])

    def test_extract_bracket_contents(self):
        # when:
        got_bracket_content = utilities.extract_bracket_contents(a_bracket_containing_string())

        # then:
        self.assertEqual(got_bracket_content, bracket_content())

    def test_extract_bracket_contents_with_no_brackets(self):
        self.assertRaises(NoContentError, utilities.extract_bracket_contents, a_normal_string())


if __name__ == '__main__':
    unittest.main()
