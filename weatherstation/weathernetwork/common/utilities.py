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

from datetime import datetime

"""General utilities functions.

Functions:
is_float:                        Determines if a string is a number.
floor_to_n:                     Floors a float to the next integer dividable by n.
ceil_to_n:                      Ceils a float to the next integer dividable by n.
"""
import math


def is_float(string):
    """Determines if a string is a number.
    
    Args:
    string:                     String to be checked.   
    
    Returns:                             
    result:                 True if the string is a number, False otherwise.
                                
    Raises:
    None
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def floor_to_n(val, n):
    """Floors a float to the next integer dividable by n.
    
    Args:
    val:                        Value to be floored.
    n:                          The number will be floored to the next integer dividable by this number.
    
    Returns:                             
    floord_val:                 Value floored to the next integer dividable by 'n'.
                                
    Raises:
    None
    """
    floored_val = math.floor(val / n) * n

    return floored_val


def ceil_to_n(val, n):
    """Ceils a float to the next integer dividable by n.
    
    Args:
    val:                        Value to be ceiled.
    n:                          The number will be ceiled to the next integer dividable by this number.
    
    Returns:                             
    ceiled_val:                 Value ceiled to the next integer dividable by 'n'.
                                
    Raises:
    None
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


class Comparable(object):
    """Mix-in class making an object comparable"""
    def __eq__(self, other):
        """Equality operator"""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        """Non-equality operator"""
        return not self.__eq__(other)
