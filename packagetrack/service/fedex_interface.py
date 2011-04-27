
from ..service import BaseInterface

class FedexInterface(BaseInterface):

    def identify(self, tracking_number):
        return len(tracking_number) in (12, 15, 22)

    def url(self, tracking_number):
        return ('http://www.fedex.com/Tracking?tracknumbers=%s'
                % tracking_number)

    def validate(self, tracking_number):
        return True
