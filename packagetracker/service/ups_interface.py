
import json
import logging
import requests
from datetime import datetime

from ..data         import TrackingInfo
from ..exceptions   import TrackFailed, InvalidTrackingNumber
from ..service      import BaseInterface

# test numbers from the documentation - note that these have invalid checksums!
TEST_NUMBERS = [
    '1Z12345E0205271688',
    '1Z12345E6605272234',
    '1Z12345E0305271640',
    '1Z12345E1305277940',
    '1Z12345E6205277936',
    '1Z648616E192760718',
    '1ZWX0692YP40636269',
    '1Z12345E1505270452',
]

ACTIVITY_STATUS_TYPE = {
    'I': 'In Transit',
    'D': 'Delivered',
    'X': 'Exception',
    'P': 'Pickup',
    'M': 'Manifest Pickup',
}
LINKROOT = "https://www.ups.com/track?loc=en_US&requester=QUIC&tracknum={tracknum}/trackdetails"

log = logging.getLogger()


class UPSInterface(BaseInterface):
    """
    UPS interface class.
    """

    click_url = 'http://wwwapps.ups.com/WebTracking/processInputRequest?TypeOfInquiryNumber=T&InquiryNumber1={num}'

    _api_urls = {
        "test":         'https://wwwcie.ups.com/rest/Track',
        "production":   'https://onlinetools.ups.com/rest/Track',
    }

    # specific exceptions for specific error codes
    _error_exceptions = {
        '151018': InvalidTrackingNumber,
        '151022': InvalidTrackingNumber,
        '154010': InvalidTrackingNumber,
        '151044': InvalidTrackingNumber,
    }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.testing:
            self.api_url = self._api_urls['test']
        else:
            self.api_url = self._api_urls['production']


    def identify(self, num):
        """
        Identify a package.

        Args:
            num (str): Tracking number

        Returns:
            bool: true if the given number is a UPS tracking number.
        """
        num = self.cleanup_number(num)
        return num.startswith('1Z') and len(num) == 18


    def validate(self, num):
        """
        Validate this tracking number, verifies its checksum.

        Args:
            num (str): tracking number

        Returns:
            bool: True if this is a valid UPS tracking number.
        """

        if not self.identify(num):
            log.debug("Number %s is not a UPS number!", num)
            return False

        num = self.cleanup_number(num)
        log.debug("Validating UPS %s", num)

        # Per documentation, test numbers have invalid checksums!
        if self.testing and num in TEST_NUMBERS:
            log.info("Tracking number %s is a test number, skipping check", num)
            return True

        checksum = calculate_checksum(num)
        test = int(num[-1:])
        log.debug("UPS %s checksum: %s, should be %s", num, checksum, test)
        return (test == checksum)


    def _build_access_request(self):
        """Build the access portion of the request"""

        return {
            'UsernameToken': {
                'Username': self.config.get('UPS', 'user_id'),
                'Password': self.config.get('UPS', 'password'),
            },
            'ServiceAccessToken': {
                'AccessLicenseNumber': self.config.get('UPS', 'license_number'),
            },
        }


    def _build_track_request(self, tracking_number):
        # Build the track portion of the request

        return {
            'Request': {
                'TransactionReference': {
                    'CustomerContext': 'track request',
                },
                'RequestOption': '1',
            },
            'InquiryNumber': tracking_number
        }


    def _build_request(self, tracking_number):
        # build the full tracking request

        return {
            'UPSSecurity': self._build_access_request(),
            'TrackRequest': self._build_track_request(tracking_number),
        }


    def _send_request(self, tracking_number):
        # make the tracking request

        body = self._build_request(tracking_number)
        log.debug('Request: %s', json.dumps(body, indent=2))

        headers = {
            'Content-Type': 'application/json',
        }
        resp = requests.post(self.api_url, data=json.dumps(body), headers=headers)
        log.debug('Response: %s', resp.json())
        data = resp.json()

        # check for fatal errors now
        if 'Fault' in data:
            self._parse_error_response(data)

        return data

    def _parse_error_response(self, rsp):
        # parse any error response, raise appropriate exceptions

        error = rsp['Fault']
        error_detail = error['detail']['Errors']['ErrorDetail']
        error_code = error_detail['PrimaryErrorCode']['Code']
        error_msg = error_detail['PrimaryErrorCode']['Description']

        log.error("Track failed: %s %s", error_code, error_msg)

        # if there's an exception specifically configured for this code,
        # use it, otherwise just use the default TrackFailed
        if error_code in self._error_exceptions:
            raise self._error_exceptions[error_code](error_msg)
        else:
            raise TrackFailed(error_msg)


    def _parse_response(self, rsp, tracking_number):
        # parse a good response

        root = rsp['TrackResponse']

        response = root['Response']
        status_code = int(response['ResponseStatus']['Code'])
        if status_code != 1:
            raise TrackFailed(response['ResponseStatus']['Description'])

        # we need the service code, some things are treated differently
        try:
            service_code = root['Shipment']['ShipmentType']['Code']
        except KeyError:
            service_code = root['Shipment']['Service']['Code']

        service_description = root['Shipment']['Service']['Description']
        if not service_description.startswith('UPS'):
            service_description = 'UPS ' + service_description


        package = root['Shipment']['Package']

        # make activites a list if it's not already
        if type(package['Activity']) != list:
            package['Activity'] = [package['Activity']]

        # this is the last activity, the one we get status info from
        activity = package['Activity'][0]

        # here's the status code, inside the Activity block
        status = activity['Status']['Description']
        status_code = activity['Status']['Code']

        last_update_date = datetime.strptime(activity['Date'], "%Y%m%d").date()
        last_update_time = datetime.strptime(activity['Time'], "%H%M%S").time()
        last_update = datetime.combine(last_update_date, last_update_time)

        # 031 = BASIC service, delivered to local P.O., so we use the
        # ShipTo address to get the city, state, country
        # this may never be considered D=Delivered, best we can do
        # is just report that the local P.O. got it.
        #
        # note this also has no SDD, so we just use the last update
        if service_code == '031':
            loc = root['Shipment']['ShipTo']['Address']
            last_location = ','.join((loc['City'],
                                      loc['StateProvinceCode'],
                                      loc['CountryCode']))
            delivery_date = last_update

        else:
            # this is a pickup, so we don't care about location
            if 'M' in status_code or 'P' in status_code:
                last_location = None

            else:
                # the last known location is interesting, but sometimes
                # not all the fields are provided.
                loc = activity['ActivityLocation']['Address']
                locvals = []
                for key in ('City', 'StateProvinceCode', 'CountryCode'):
                    if key in loc:
                        locvals.append(loc[key])
                last_location = ','.join(locvals)

            # Delivery date is the last_update if delivered, otherwise
            # the estimated delivery date
            if status_code == 'D':
                delivery_date = last_update

            elif 'RescheduledDeliveryDate' in package:
                delivery_date = datetime.strptime(
                    package['RescheduledDeliveryDate'], "%Y%m%d")
            elif 'ScheduledDeliveryDate' in root['Shipment']:
                delivery_date = datetime.strptime(
                    root['Shipment']['ScheduledDeliveryDate'], "%Y%m%d")
            else:
                delivery_date = None


        # Delivery detail may not always be available either
        if 'Description' in activity['ActivityLocation']:
            delivery_detail = activity['ActivityLocation']['Description']
        else:
            delivery_detail = status

        trackinfo = TrackingInfo(
            tracking_number = tracking_number,
            last_update     = last_update,
            delivery_date   = delivery_date,
            status          = status,
            location        = last_location,
            delivery_detail = delivery_detail,
            service         = service_description,
            link            = LINKROOT.format(tracknum = tracking_number),
        )


        # add a single event, UPS doesn't seem to support multiple?

        for e in package['Activity']:
            location = None
            if 'ActivityLocation' in e:
                loc = e['ActivityLocation']['Address']
                if 'City' in loc:
                    location = ','.join((loc['City'],
                                        loc['StateProvinceCode'],
                                        loc['CountryCode']))

            edate = datetime.strptime(e['Date'], "%Y%m%d").date()
            etime = datetime.strptime(e['Time'], "%H%M%S").time()
            timestamp = datetime.combine(edate, etime)
            trackinfo.add_event(
                location = location,
                detail = e['Status']['Description'],
                date = timestamp,
            )

        return trackinfo


    def track(self, num):
        """
        Track a UPS package by number

        Args:
            num: UPS tracking number

        Returns:
            str: tracking info

        Raises:
            InvalidTrackingnumber
            TrackFailed
        """

        if not self.validate(num):
            log.debug("Invalid tracking number: %s", num)
            raise InvalidTrackingNumber(num)

        resp = self._send_request(num)
        return self._parse_response(resp, num)


def calculate_checksum(num):
    """
    Calculate the checksum on a UPS tracking number.

    Args:
        num: tracking number

    Returns:
        int: checksum
    """

    testnum = num[2:-1]

    even_total = odd_total = 0
    for ii, digit in enumerate(testnum.upper()):
        try:
            digit = int(digit)
        except ValueError:
            digit = int(ord(digit) - 63) % 10

        if (ii + 1) % 2:
            odd_total += digit
        else:
            even_total += digit

    total = odd_total + even_total * 2
    checksum = total % 10
    if checksum > 0:
        checksum = 10 - checksum

    return checksum
