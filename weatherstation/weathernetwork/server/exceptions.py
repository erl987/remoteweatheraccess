class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class NotExistingError(Error):
    """Raised when a queried database item does not exists.
    """

    def __init__(self, msg):
        """
        Constructor.
        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class AlreadyExistingError(Error):
    """Raised when a database item that should be added already exists.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        """
        Constructor.
        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg


class InvalidConfigFileError(Error):
    """Raise when a config file is invalid.
    """

    def __init__(self, msg):
        """
        Constructor.
        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg
