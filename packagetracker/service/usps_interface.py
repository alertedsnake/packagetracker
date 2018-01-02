import logging
import requests
from six.moves.urllib_parse import quote as urlquote
from datetime import datetime

from ..data         import TrackingInfo
from ..service      import BaseInterface
from ..exceptions   import TrackFailed, InvalidTrackingNumber
from ..xml_dict     import xml_to_dict

log = logging.getLogger()


class USPSInterface(BaseInterface):
    """
    USPS interface class.
    """

    click_url = 'http://trkcnfrm1.smi.usps.com/PTSInternetWeb/InterLabelInquiry.do?origTrackNum={num}'

    _api_urls = {
        'secure_test': 'https://secure.shippingapis.com/ShippingAPITest.dll?API=TrackV2&XML=',
        'test':        'http://testing.shippingapis.com/ShippingAPITest.dll?API=TrackV2&XML=',
        'production':  'http://production.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML=',
        'secure':      'https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML=',
    }

    # names of USPS service types
    service_types = {
        'EA': 'express mail',
        'EC': 'express mail international',
        'CP': 'priority mail international',
        'RA': 'registered mail',
        'RF': 'registered foreign',
        #'EJ': 'something?',
    }


    def __init__(self, *args, **kwargs):
        super(USPSInterface, self).__init__(*args, **kwargs)

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
            bool: true if this service can track this package
        """
        ##
        ## TODO: verify this:
        ## Apparently USPS uses 22-digit numbers for the *not-trackable*
        ## delivery confirmation numbers.
        ##
        ## Actual trackable numbers are 13-characters.
        ##
        num = self.cleanup_number(num)
        return (
            (num.isdigit() and len(num) == 22) or
            (num.isdigit() and len(num) == 10) or
            (
                len(num) == 13 and
                num[0:2].isalpha() and
                num[2:9].isdigit() and
                num[11:13].isalpha()
            )
        )


    def validate(self, num):
        """Validate the given tracking number.

        Returns:
            bool
        """
        if not self.identify(num):
            log.debug("Number {} is not a USPS number!".format(num))
            return False

        log.debug("Validating USPS {}".format(num))

        num = self.cleanup_number(num)

        # we can only do this with numerics!
        if (num.isdigit() and len(num) == 22):
            checksum = calculate_checksum(num)
            test = int(num[-1])
            log.debug("USPS {} checksum: {}, should be {}".format(num, checksum, test))
            return (checksum == test)

        return True


    def track(self, num):
        """
        Track a USPS package.

        Args:
            num (str): Tracking number

        Raises:
            InvalidTrackingNumber
            TrackFailed
        """
        if not self.validate(num):
            log.debug("Invalid tracking number: {}".format(num))
            raise InvalidTrackingNumber(num)

        resp = self._send_request(num)
        return self._parse_response(resp, num)


    def _build_request(self, num):
        # Build a request

        return '<TrackFieldRequest USERID="%s"><TrackID ID="%s"/></TrackFieldRequest>' % (
                self.config.get('USPS', 'userid'), num)


    def _parse_response(self, raw, num):
        # parse the response, this is all XML.

        log.debug(raw)
        rsp = xml_to_dict(raw)

        # this is a system error
        if 'Error' in rsp:
            error = rsp['Error']['Description']
            raise TrackFailed(error)

        # this is a result with an error, like "no such package"
        if 'Error' in rsp['TrackResponse']['TrackInfo']:
            error = rsp['TrackResponse']['TrackInfo']['Error']['Description']
            raise TrackFailed(error)

        # make sure the events list is a list
        # note that sometimes there's no TrackDetail
        events = []
        if 'TrackDetail' in rsp['TrackResponse']['TrackInfo']:
            events = rsp['TrackResponse']['TrackInfo']['TrackDetail']
            if type(events) != list:
                events = [events]

        summary = rsp['TrackResponse']['TrackInfo']['TrackSummary']
        last_update = self._getTrackingDate(summary)
        last_location = self._getTrackingLocation(summary)

        # status is the first event's status
        status = summary['Event']

        # USPS doesn't return this, so we work it out from the tracking number
        service_code = num[0:2]
        service_description = self.service_types.get(service_code, 'USPS')

        trackinfo = TrackingInfo(
                            tracking_number = num,
                            last_update     = last_update,
                            delivery_date   = last_update,
                            status          = status,
                            location        = last_location,
                            delivery_detail = None,
                            service         = service_description,
                    )

        # add the last event if delivered, USPS doesn't duplicate
        # the final event in the event log, but we want it there
        if status == 'DELIVERED':
            trackinfo.add_event(
                location = last_location,
                detail = status,
                date = last_update,
            )

        for e in events:
            trackinfo.add_event(
                location = self._getTrackingLocation(e),
                date     = self._getTrackingDate(e),
                detail   = e['Event'],
            )

        return trackinfo


    def _send_request(self, num):
        # Send the right request

        # pick the USPS API server, if in the config file
        if self.config.has_option('USPS', 'server'):
            baseurl = self._api_urls[self.config.get('USPS', 'server')]
        else:
            baseurl = self.api_url

        url = "%s%s" % (baseurl, urlquote(self._build_request(num)))
        resp = requests.get(url)
        return resp.text


    def _getTrackingDate(self, node):
        """Returns a datetime object for the given node's
        <EventTime> and <EventDate> elements"""

        # in some cases, there's no time, like in
        # "shipping info received"
        if not node['EventTime']:
            return datetime.strptime(node['EventDate'], '%B %d, %Y').date()

        return datetime.combine(
                    datetime.strptime(node['EventDate'], '%B %d, %Y').date(),
                    datetime.strptime(node['EventTime'], '%I:%M %p').time())


    def _getTrackingLocation(self, node):
        """Returns a location given a node that has
            EventCity, EventState, EventCountry elements"""

        return ','.join((
                node['EventCity'],
                node['EventState'],
                node['EventCountry'] or 'US'
        ))


def calculate_checksum(num):
    """
    Calculate the checksum on a USPS tracking number.

    Args:
        num: tracking number

    Returns:
        int: checksum
    """

    even = sum(map(int, num[-2::-2]))
    odd = sum(map(int, num[-3::-2]))
    checksum = even * 3 + odd
    return (10 - (checksum % 10)) % 10

