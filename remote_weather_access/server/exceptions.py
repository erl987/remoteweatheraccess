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


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class NotExistingError(Error):
    """Raised when a queried database item does not exists."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class AlreadyExistingError(Error):
    """Raised when a database item that should be added already exists."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class InvalidConfigFileError(Error):
    """Raise when a config file is invalid."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class NoContentError(Error):
    """Raised when the requested content does not exist."""
    def __init__(self, msg):
        """
        Constructor.

        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg