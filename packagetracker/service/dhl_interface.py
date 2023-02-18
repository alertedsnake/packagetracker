import logging
import re
import requests
from datetime import datetime

from ..data         import TrackingInfo
from ..exceptions   import TrackFailed, InvalidTrackingNumber
from ..service      import BaseInterface

LINKROOT = "https://www.dhl.com/us-en/home/tracking.html?tracking-id={tracknum}&submit=1"

log = logging.getLogger()


class DHLClient(requests.sessions.Session):
    def __init__(self, apikey: str, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.headers.update({
            "DHL-API-Key":  apikey,
            "Accept":       "application/json",
        })


class DHLInterface(BaseInterface):
    """
    DHL interface class.
    """

    _api_urls = {
        "production": "https://api-eu.dhl.com/track/shipments",
        "test":       "https://api-eu.dhl.com/track/shipments",
        # this is valid but apparently I can't access it?
        #"test":       "https://api-test.dhl.com/track/shipments",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.testing:
            self.api_url = self._api_urls['test']
        else:
            self.api_url = self._api_urls['production']

        self.client = DHLClient(self.config.get('DHL', 'apikey'))


    def identify(self, num):
        """
        Identify a package.

        Args:
            num (str): Tracking number

        Returns:
            bool: true if the given number is a tracking number.
        """
        # https://www.easyship.com/blog/dhl-tracking

        return self.validate(num)


    def validate(self, num):
        """
        Validate this tracking number.

        Args:
            num (str): tracking number

        Returns:
            bool: True if this is a valid tracking number.
        """
        if len(num) == 10:
            # DHL Express
            if num.startswith("000") and num.isdigit():
                return True

            # DHL Express - doesn't catch "a similar variation"
            # as the docs say, whatever that means
            if m := re.match(r'^(?:JJD01|JJD00|JVGL)(.+)$', num):
                if m.group(1).isdigit():
                    return True

            # DHL Parcel
            if m := re.match(r'^(?:3S|JVGL|JJD)(.+)$', num):
                if m.group(1).isdigit():
                    return True

        # DHL eCommerce - doesn't catch the one which starts
        # with "up to 5 letters" because how do I do that sanely
        if (len(num) >= 10 and len(num) <= 39
                and re.match(r'^(?:GM|LX|RX)', num)):
            return True

        return False


    def _parse_response(self, resp, num):
        data = resp.json()

        # test errors
        if 'status' in data:
            log.error("Track failed: %s %s", data['status'], data['detail'])

            if data['status'] == 404:
                raise InvalidTrackingNumber(data.get('detail'))
            if data['status'] == 401:
                raise TrackFailed(data.get('detail'))

        # we only ever have one shipment here
        shipment = data["shipments"][0]

        # status:
        # ["pre-transit","transit","delivered","failure","unknown"]

        locstring = self._format_location(
            shipment["status"]["location"]["address"])

        last_update = datetime.strptime(
            shipment["status"]["timestamp"], "%Y-%m-%dT%H:%M:%S")

        # if delivered, use the last status as the delivery date
        if shipment["status"]["status"] == 'delivered':
            delivery_date = last_update
        else:
            delivery_date = None

        trackinfo = TrackingInfo(
            tracking_number = shipment["id"],
            last_update     = last_update,
            status          = shipment["status"]["status"],
            location        = locstring,
            delivery_detail = shipment["status"].get("description"),
            delivery_date   = delivery_date,
            service         = shipment["service"],
            link            = LINKROOT.format(tracknum = num),
        )

        return trackinfo


    def _format_location(self, data):
        out = data["addressLocality"]

        if "countryCode" in data:
            out = ",".join((out, data["countryCode"]))

        return out


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

        #if not self.validate(num):
        #    log.debug("Invalid tracking number: %s", num)
        #    raise InvalidTrackingNumber(num)

        resp = self.client.get(self.api_url, params = {
            'trackingNumber': num,
        })
        return self._parse_response(resp, num)

