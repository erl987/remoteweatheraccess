# RemoteWeatherAccess - Weather network connecting to remote stations
# Copyright(C) 2013-2017 Ralf Rettig (info@personalfme.de)
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

import math
from datetime import datetime

from server.exceptions import NoContentError


def is_float(string):
    """
    Determines if a string is a number.

    :param string:              string to be checked
    :type string:               str
    :return:                    True if the string is a number, False otherwise
    :rtype:                     bool
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def floor_to_n(val, n):
    """
    Floors a float to the next real number dividable by n.

    :param val:                 value to be floored
    :type val:                  float
    :param n:                   the number will be floored to the next real number dividable by this number
    :type n:                    float
    :return:                    value floored to the next real number dividable by 'n'
    :rtype:                     float
    """
    floored_val = math.floor(val / n) * n

    return floored_val


def ceil_to_n(val, n):
    """
    Ceils a float to the next real number dividable by n.

    :param val:                 value to be ceiled
    :type val:                  float
    :param n:                   the number will be ceiled to the next real number dividable by this number
    :type n:                    float
    :return:                    value ceiled to the next real number dividable by 'n'
    :rtype:                     float
    """
    ceiled_val = math.ceil(val / n) * n

    return ceiled_val


def consolidate_ranges(ranges):
    """
    Consolidates a list of time ranges by merging all overlapping ranges.
    
    :param ranges:              list of unmerged time ranges
    :type ranges:               list of datetime tuples
    :return:                    consolidated list of time ranges
    :rtype:                     list of datetime tuples
    """
    result = []
    current_begin = datetime.min
    current_end = datetime.min

    for begin, end in sorted(ranges):
        if begin > current_end:
            # a new range is starting
            result.append((begin, end))
            current_begin, current_end = begin, end
        else:
            # the current range overlaps and extends the previous range
            current_end = max(current_end, end)
            result[-1] = (current_begin, current_end)

    return result


def extract_bracket_contents(data_string):
    """
    Extracts the contents of the first brackets from the given string.

    :param data_string:         string containing brackets
    :type data_string:          str
    :return:                    the content of the first bracket
    :rtype:                     str
    :raise NoContentError:      if the data string does not contain opening and closing brackets
    """
    if '(' not in data_string or ')' not in data_string:
        raise NoContentError("The string does not contain brackets")

    bracket_contents = str.split(str.split(data_string, '(')[1], ')')[0]

    return bracket_contents


class Comparable(object):
    """Mix-in class making an object comparable"""
    def __eq__(self, other):
        """
        Equality operator.

        :param other:           object to be compared
        :return:                True if the object are equal, False otherwise
        :rtype:                 bool
        """
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        """
        Non-equality operator.

        :param other:           object to be compared
        :return:                True if the objects are not equal, False otherwise
        :rtype:                 bool
        """
        return not self.__eq__(other)
