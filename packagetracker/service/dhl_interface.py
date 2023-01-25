import json
import logging
import requests
from datetime import datetime

from ..data         import TrackingInfo
from ..exceptions   import TrackFailed, InvalidTrackingNumber
from ..service      import BaseInterface

TEST_NUMBERS = [
]

log = logging.getLogger()


class DHLClient(requests.sessions.Session):
    def __ini__(self, apikey: str, *args, **kwargs):

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
        "testing":    "https://api-test.dhl.com/track/shipments",
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
            bool: true if the given number is a UPS tracking number.
        """
        return True


    def validate(self, num):
        """
        Validate this tracking number, verifies its checksum.

        Args:
            num (str): tracking number

        Returns:
            bool: True if this is a valid UPS tracking number.
        """
        return True


    def ._parse_response(self, resp, num):
        data = resp.json()["shipments"][0]

        location = data["status"]["location"]["address"]
        locstring = ",".join((
            location["addressLocality"],
            location["countryCode"],
        )

        trackinfo = TrackingInfo(
            tracking_number = num,
            last_update     = data["shipments"["id"],
            delivery_date   = data["status"]["timestamp"],
            status          = data["status"]["status"],
            location        = locstring,
            delivery_detail = data["status"]["remark"],
            service         = service_description,
            link            = "foo",
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

        #if not self.validate(num):
        #    log.debug("Invalid tracking number: %s", num)
        #    raise InvalidTrackingNumber(num)

        resp = self.client.get(self.api_url, params = {
            'trackingNumber': num,
        })
        return self._parse_response(resp, num)

