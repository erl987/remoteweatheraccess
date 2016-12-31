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

import sys
import tblib.pickling_support
tblib.pickling_support.install()


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class FileParseError(Error):
    """Raised when a data file could not be parsed correctly due to wrong format."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class PCWetterstationFileParseError(FileParseError):
    """Raised when a PC Wetterstation data file could not be parsed correctly due to wrong format."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        super().__init__(msg)


class DatasetFormatError(FileParseError):
    """Raised when a weather dataset lacks required sensors."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        super().__init__(msg)


class RunInNotAllowedProcessError(Error):
    """Raised when an operation is run in a not allowed process."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        super().__init__(msg)


class DelayedException(Exception):
    """Exception base class that can be reraised in other processes including the traceback"""
    def __init__(self, ee):
        """
        Constructor.

        :param ee:      exception to be reraised
        :type ee:       Exception
        """
        self.ee = ee
        __,  __, self.tb = sys.exc_info()

    def re_raise(self):
        """
        Reraises the exception with the original traceback now.
        """
        raise self.ee.with_traceback(self.tb)
