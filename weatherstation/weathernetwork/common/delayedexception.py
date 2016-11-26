import sys
import tblib.pickling_support
tblib.pickling_support.install()


class DelayedException(object):
    """Exception base class that can be reraised in other processes including the traceback"""

    def __init__(self, ee):
        self.ee = ee
        __,  __, self.tb = sys.exc_info()

    def re_raise(self):
        raise self.ee.with_traceback(self.tb)
