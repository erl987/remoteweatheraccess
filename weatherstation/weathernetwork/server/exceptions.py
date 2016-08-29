class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class NotExistingError(Error):
    """Raised when a queried database item does not exists.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg


class AlreadyExistingError(Error):
    """Raised when a database item that should be added already exists.

    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg
