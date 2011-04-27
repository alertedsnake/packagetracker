from datetime import datetime, date, time

from fedex.config import FedexConfig
from fedex.services.track_service import FedexTrackRequest

import packagetrack
from ..data import TrackingInfo
from ..service import BaseInterface, TrackFailed

class FedexInterface(BaseInterface):

    def __init__(self):
        self.cfg = None

    def identify(self, tracking_number):
        return len(tracking_number) in (12, 15)

    def track(self, tracking_number):
        track = FedexTrackRequest(self.get_cfg())

        track.TrackPackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
        track.TrackPackageIdentifier.Value = tracking_number

        # Fires off the request, sets the 'response' attribute on the object.
        track.send_request()

        # TODO: I haven't actually seen an unsuccessful query yet
        if track.response.HighestSeverity != "SUCCESS":
            raise TrackFailed("%d: %s" % (
                    track.response.Notifications[0].Code,
                    track.response.Notifications[0].LocalizedMessage
                    ))

        return self.parse_response(track.response.TrackDetails[0])


    def url(self, tracking_number):
        return ('http://www.fedex.com/Tracking?tracknumbers=%s'
                % tracking_number)


    def parse_response(self, rsp):
        """Parse the track response and return a TrackingInfo object"""

        # test status code, return actual delivery time if package
        # was delivered, otherwise estimated target time
        if rsp.StatusCode == 'DL':
            delivery_date = rsp.ActualDeliveryTimestamp
            last_update = delivery_date
            location = ','.join((
                                rsp.ActualDeliveryAddress.City,
                                rsp.ActualDeliveryAddress.StateOrProvinceCode,
                                rsp.ActualDeliveryAddress.CountryCode,
                            ))

        else:
            delivery_date = rsp.EstimatedDeliveryTimestamp
            last_update = rsp.Events[0].Timestamp
            location = ','.join((
                                rsp.Events[0].Address.City,
                                rsp.Events[0].Address.StateOrProvinceCode,
                                rsp.Events[0].Address.CountryCode,
                            ))


        return TrackingInfo(
                    last_update     = last_update,
                    delivery_date   = delivery_date,
                    status          = rsp.StatusDescription,
                    location        = location,
                )


    def get_cfg(self):
        """Makes and returns a FedexConfig object from the packagetrack
           configuration.  Caches it, so it doesn't create each time."""

        config = packagetrack.config

        # got one cached, so just return it
        if self.cfg:
            return self.cfg

        self.cfg = FedexConfig(
            key                 = config.get('FedEx', 'key'),
            password            = config.get('FedEx', 'password'),
            account_number      = config.get('FedEx', 'account_number'),
            meter_number        = config.get('FedEx', 'meter_number'),
            use_test_server     = False,
            express_region_code = 'US',
        )

        # these are optional, and afaik, not really used for tracking
        # at all, but you can still set them, so....
        if config.has_option('FedEx', 'express_region_code'):
            self.cfg.express_region_code = config.get('FedEx',
                                            'express_region_code')

        if config.has_option('FedEx', 'integrator_id'):
            self.cfg.integrator_id = config.get('FedEx',
                                            'integrator_id')

        if config.has_option('FedEx', 'use_test_server'):
            self.cfg.use_test_server = config.getboolean('FedEx',
                                            'use_test_server')

        return self.cfg

