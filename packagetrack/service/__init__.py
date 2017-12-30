
class TrackFailed(Exception):
    pass


class InvalidTrackingNumber(Exception):
    pass


class BaseInterface(object):
    """Base class for tracking interfaces"""

    def __init__(self, config, testing=False):
        self.config = config
        self.testing = testing

    def identify(self, tracking_number):
        raise NotImplementedError

    def track(self, tracking_number):
        raise NotImplementedError

