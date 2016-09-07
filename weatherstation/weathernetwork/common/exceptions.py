class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class FileParseError(Error):
    """Raised when a data file could not be parsed correctly due to wrong format."""

    def __init__(self,msg):
        """
        Constructor.
        :param msg:     error message description
        :type msg:      string
        """
        self.msg = msg        



class PCWetterstationFileParseError(FileParseError):
    """Raised when a PC Wetterstation data file could not be parsed correctly due to wrong format.
    """

    def __init__(self, msg):
        """
        Constructor.
        :param msg:     error message description
        :type msg:      string
        """
        super(PCWetterstationFileParseError, self).__init__(msg)