
class TrackFailed(Exception):
    pass

class BaseInterface(object):

    def identify(self, tracking_number):
        raise NotImplementedError

    def track(self, tracking_number):
        raise NotImplementedError

