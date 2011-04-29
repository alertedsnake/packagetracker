
class TrackFailed(Exception):
    pass

class InvalidTrackingNumber(Exception):
    pass

class BaseInterface(object):
    """Base class for tracking interfaces"""

    def identify(self, tracking_number):
        raise NotImplementedError

    def track(self, tracking_number):
        raise NotImplementedError

