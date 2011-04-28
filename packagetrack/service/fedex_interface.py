from datetime import datetime, date, time

from fedex.config import FedexConfig
from fedex.base_service import FedexError
from fedex.services.track_service import FedexTrackRequest, FedexInvalidTrackingNumber

import packagetrack
from ..data import TrackingInfo
from ..service import BaseInterface, TrackFailed, InvalidTrackingNumber

class FedexInterface(BaseInterface):

    def __init__(self):
        self.cfg = None

    def identify(self, tracking_number):
        return len(tracking_number) in (12, 15, 20, 22)

    def track(self, tracking_number):
        if not self.validate(tracking_number):
            raise InvalidTrackingNumber()

        track = FedexTrackRequest(self._get_cfg())

        track.TrackPackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
        track.TrackPackageIdentifier.Value = tracking_number

        # Fires off the request, sets the 'response' attribute on the object.
        try:
            track.send_request()
        except FedexInvalidTrackingNumber, e:
            raise InvalidTrackingNumber(e)
        except FedexError, e:
            raise TrackFailed(e)

        # TODO: I haven't actually seen an unsuccessful query yet
        if track.response.HighestSeverity != "SUCCESS":
            raise TrackFailed("%d: %s" % (
                    track.response.Notifications[0].Code,
                    track.response.Notifications[0].LocalizedMessage
                    ))

        return self._parse_response(track.response.TrackDetails[0])


    def url(self, tracking_number):
        return ('http://www.fedex.com/Tracking?tracknumbers=%s'
                % tracking_number)


    def _parse_response(self, rsp):
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
            location = self._getTrackingLocation(rsp.Events[0])


        # a new tracking info object
        trackinfo = TrackingInfo(
                    last_update     = last_update,
                    delivery_date   = delivery_date,
                    status          = rsp.StatusDescription,
                    location        = location,
                )

        # now add the events
        for e in rsp.Events:
            trackinfo.addEvent(
                location = self._getTrackingLocation(e),
                date     = e.Timestamp,
                detail   = e.EventDescription,
            )

        return trackinfo


    def _getTrackingLocation(self, e):
        """Returns a nicely formatted location for a given event"""
        try:
            return ','.join((
                            e.Address.City,
                            e.Address.StateOrProvinceCode,
                            e.Address.CountryCode,
                        ))
        except:
            return None


    def _get_cfg(self):
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


    def validate(self, tnum):
        """Validate the tracking number"""

        if len(tnum) == 12:
            return self._validate_express(tnum)

        elif (len(tnum) == 15):
            return self._validate_ground96(tnum)

        elif (len(tnum) == 22) and tnum.startswith('96'):
            return self._validate_ground96(tnum)

        elif (len(tnum) == 20) and tnum.startswith('00'):
            return self._validate_ssc18(tnum)

        return False


    def _validate_ground96(self, tracking_number):
        """Validates ground code 128 ("96") bar codes

            15-digit form:

                    019343586678996
        shipper ID: -------
        package ID:        -------
        checksum:                 -

                22-digit form:
                    9611020019343586678996
        UCC/EAN id: --
        SCNC:         --
        class of svc:   --
        shipper ID:        -------
        package ID:               -------
        checksum:                        -

        """

        rev = tracking_number[::-1]

        eventotal = 0
        oddtotal = 0
        for i in range(1,14):
            if i % 2:
                eventotal += int(rev[i])
            else:
                oddtotal += int(rev[i])

        check = 10 - ((eventotal * 3 + oddtotal) % 10)

        # compare with the checksum digit, which is the last digit
        return check == int(tracking_number[-1:])

    def _validate_ssc18(self, tracking_number):
        """Validates SSC18 tracking numbers"""

        rev = tracking_number[::-1]

        eventotal = 0
        oddtotal = 0
        for i in range(1,18):
            if i % 2:
                eventotal += int(rev[i])
            else:
                oddtotal += int(rev[i])

        check = 10 - ((eventotal * 3 + oddtotal) % 10)

        # compare with the checksum digit, which is the last digit
        return check == int(tracking_number[-1:])


    def _validate_express(self, tracking_number):
        """Validates Express tracking numbers"""

        basenum = tracking_number[0:10]

        sums = []
        mult = 1
        total = 0
        for digit in basenum[::-1]:
            sums.append(int(digit) * mult)
            total = total + (int(digit) * mult)

            if mult == 1: mult = 3
            if mult == 3: mult = 7
            if mult == 7: mult = 1

        check = total % 11
        if check == 10:
            check = 0

        # compare with the checksum digit, which is the last digit
        return check == int(tracking_number[-1:])

