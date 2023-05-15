import logging

from fedex.config import FedexConfig
from fedex.base_service import FedexError
from fedex.services.track_service import FedexTrackRequest, FedexInvalidTrackingNumber

from ..data         import TrackingInfo
from ..exceptions   import TrackFailed, InvalidTrackingNumber
from ..service      import BaseInterface

log = logging.getLogger()

# test numbers from the documentation - note that these have invalid checksums!
TEST_NUMBERS = (
    '449044304137821',
    '149331877648230',
    '020207021381215',
    '403934084723025',
    '920241085725456',
    '568838414941',
    '039813852990618',
    '231300687629630',
    '797806677146',
    '377101283611590',
    '852426136339213',
    '797615467620',
    '957794015041323',
    '076288115212522',
    '581190049992',
    '122816215025810',
    '843119172384577',
    '070358180009382',
)

LINKROOT = "https://www.fedex.com/fedextrack/?trknbr={tracknum}"


class FedexInterface(BaseInterface):
    """
    FedEx interface class.
    """

    click_url = 'http://www.fedex.com/Tracking?tracknumbers={num}'

    def __init__(self, *args, **kwargs):
        self.cfg = None
        super().__init__(*args, **kwargs)


    def identify(self, num):
        """
        Identify a FedEx package

        Args:
            num (str): Tracking number

        Returns:
            bool: true if this is a FedEx tracking number
        """
        return num.isdigit() and (len(num) in (12, 15, 20, 22))


    def track(self, num):
        """
        Track a FedEx package.

        Args:
            num (str, int): tracking number

        Raises:
            InvalidTrackingNumber
            TrackFailed
        """
        # maybe we got an int? That works for FedEx.
        if isinstance(num, int):
            num = str(num)

        #if not self.validate(num):
        #    raise InvalidTrackingNumber()

        track = FedexTrackRequest(self._get_cfg())

        # Track by Tracking Number
        track.SelectionDetails.PackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
        track.SelectionDetails.PackageIdentifier.Value = num
        #del track.SelectionDetails.OperatingCompany

        track.IncludeDetailedScans = True

        # Fires off the request, sets the 'response' attribute on the object.
        try:
            track.send_request()
        except FedexInvalidTrackingNumber as e:
            raise InvalidTrackingNumber(e)
        except FedexError as e:
            raise TrackFailed(e)

        #from fedex.tools.conversion import sobject_to_json
        #print(sobject_to_json(track.response))

        return self._parse_response(track.response.CompletedTrackDetails[0].TrackDetails[0], num)

    def _parse_response(self, rsp, tracking_number):
        """Parse the track response and return a TrackingInfo object"""

        if hasattr(rsp, 'Notification'):
            if rsp.Notification.Severity in ('ERROR', 'FAILURE'):
                raise TrackFailed('{}: {}'.format(
                    rsp.Notification.Code,
                    rsp.Notification.LocalizedMessage))

        status = 'In transit'

        # test status code, return actual delivery time if package
        # was delivered, otherwise estimated target time
        if hasattr(rsp, 'StatusDetail.Code') and rsp.StatusDetail.Code == 'DL':
            delivery_date = rsp.ActualDeliveryTimestamp

            # this may not be present
            try:
                delivery_detail = rsp.Events[0].StatusExceptionDescription
            except AttributeError:
                delivery_detail = None

            last_update = delivery_date
            location = ','.join((
                                rsp.ActualDeliveryAddress.City,
                                rsp.ActualDeliveryAddress.StateOrProvinceCode,
                                rsp.ActualDeliveryAddress.CountryCode,
                                ))
            status = 'Delivered'

        else:
            delivery_detail = None
            last_update = None
            location = None

            try:
                delivery_date = rsp.EstimatedDeliveryTimestamp
            except AttributeError:
                delivery_date = None

            if hasattr(rsp, 'Events'):
                last_update = rsp.Events[0].Timestamp
                location = self._getTrackingLocation(rsp.Events[0])

            if hasattr(rsp, 'ServiceCommitMessage'):
                status = rsp.ServiceCommitMessage


        # a new tracking info object
        trackinfo = TrackingInfo(
                    tracking_number = tracking_number,
                    last_update     = last_update,
                    status          = status,
                    location        = location,
                    delivery_date   = delivery_date,
                    delivery_detail = delivery_detail,
                    service         = rsp.Service.Type,
                    link            = LINKROOT.format(tracknum = tracking_number),
                )

        # now add the events
        if hasattr(rsp, 'Events'):
            for e in rsp.Events:
                trackinfo.add_event(
                    location = self._getTrackingLocation(e),
                    date     = e.Timestamp,
                    detail   = e.EventDescription,
                )

        return trackinfo


    def _getTrackingLocation(self, e):
        """Returns a nicely formatted location for a given event."""
        try:
            return ','.join((
                            e.Address.City,
                            e.Address.StateOrProvinceCode,
                            e.Address.CountryCode,
                            ))
        except Exception:
            return None


    def _get_cfg(self):
        """
        Makes and returns a FedexConfig object from the packagetrack
        configuration.  Caches it, so it doesn't create each time.
        """

        # got one cached, so just return it
        if self.cfg:
            return self.cfg

        self.cfg = FedexConfig(
            key                 = self.config.get('FedEx', 'key'),
            password            = self.config.get('FedEx', 'password'),
            account_number      = self.config.get('FedEx', 'account_number'),
            meter_number        = self.config.get('FedEx', 'meter_number'),
            use_test_server     = False,
            express_region_code = 'US',
        )

        # these are optional, and afaik, not really used for tracking
        # at all, but you can still set them, so....
        if self.config.has_option('FedEx', 'express_region_code'):
            self.cfg.express_region_code = self.config.get('FedEx', 'express_region_code')

        if self.config.has_option('FedEx', 'integrator_id'):
            self.cfg.integrator_id = self.config.get('FedEx', 'integrator_id')

        if self.testing:
            self.cfg.use_test_server = True
        elif self.config.has_option('FedEx', 'use_test_server'):
            self.cfg.use_test_server = self.config.getboolean('FedEx', 'use_test_server')

        return self.cfg


    def validate(self, num):
        """
        Validate the given tracking number.

        Args:
            num (str): tracking number

        Returns:
            bool: True if the number is valid.
        """

        if len(num) == 12:
            log.debug("%s is express", num)
            return self._validate_express(num)

        elif (len(num) == 15):
            log.debug("%s is ground96", num)
            return self._validate_ground96(num)

        elif (len(num) == 22) and num.startswith('96'):
            log.debug("%s is ground96 #2", num)
            return self._validate_ground96(num)

        elif (len(num) == 20) and num.startswith('00'):
            log.debug("%s is ssc18", num)
            return self._validate_ssc18(num)

        log.debug("%s - can't validate?", num)
        return False


    def _validate_ground96(self, num):
        """Validates ground code 128 ("96") bar codes

        15-digit form::

                        019343586678996
            shipper ID: -------
            package ID:        -------
            checksum:                 -

        22-digit form::
                        9611020019343586678996
            UCC/EAN id: --
            SCNC:         --
            class of svc:   --
            shipper ID:        -------
            package ID:               -------
            checksum:                        -

        Args:
            num (str): tracking number

        Returns:
            bool: True if the number is valid.

        """
        # Per documentation, test numbers have invalid checksums!
        if self.testing and num in TEST_NUMBERS:
            log.info("Tracking number %s is a test number, skipping check", num)
            return True

        rev = num[::-1]

        eventotal = 0
        oddtotal = 0
        for i in range(1, 15):
            if i % 2:
                eventotal += int(rev[i])
            else:
                oddtotal += int(rev[i])

        checksum = 10 - ((eventotal * 3 + oddtotal) % 10)
        test = int(num[-1:])
        # compare with the checksum digit, which is the last digit
        log.debug("ground96 %s: checksum: %s should be %s", num, checksum, test)
        return (test == checksum)


    def _validate_ssc18(self, num):
        """
        Validates SSC18 tracking numbers

        Args:
            num (str): tracking number

        Returns:
            bool: True if the number is valid.
        """
        # Per documentation, test numbers have invalid checksums!
        if self.testing and num in TEST_NUMBERS:
            log.info("Tracking number %s is a test number, skipping check", num)
            return True

        rev = num[::-1]

        eventotal = 0
        oddtotal = 0
        for i in range(1, 19):
            if i % 2:
                eventotal += int(rev[i])
            else:
                oddtotal += int(rev[i])

        check = 10 - ((eventotal * 3 + oddtotal) % 10)

        # compare with the checksum digit, which is the last digit
        return check == int(num[-1:])


    def _validate_express(self, num):
        """Validates Express tracking numbers

        Args:
            num (str): tracking number

        Returns:
            bool: True if the number is valid.
        """
        # Per documentation, test numbers have invalid checksums!
        if self.testing and num in TEST_NUMBERS:
            log.info("Tracking number %s is a test number, skipping check", num)
            return True

        basenum = num[0:10]

        sums = []
        mult = 1
        total = 0
        for digit in basenum[::-1]:
            sums.append(int(digit) * mult)
            total = total + (int(digit) * mult)

            if mult == 1:
                mult = 3
            if mult == 3:
                mult = 7
            if mult == 7:
                mult = 1

        check = total % 11
        if check == 10:
            check = 0

        # compare with the checksum digit, which is the last digit
        return check == int(num[-1:])
