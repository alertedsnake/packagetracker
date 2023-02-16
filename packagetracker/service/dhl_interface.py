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

        # if delivered, use the last status as the delivery date
        if shipment["status"]["status"] == 'delivered':
            delivery_date = shipment["status"]["timestamp"]
        else:
            delivery_date = None

        trackinfo = TrackingInfo(
            tracking_number = shipment["id"],
            last_update     = datetime.strptime(
                shipment["status"]["timestamp"], "%Y-%m-%dT%H:%M:%S").time(),
            status          = shipment["status"]["status"],
            location        = locstring,
            delivery_detail = shipment["status"].get("description"),
            delivery_date   = delivery_date,
            service         = shipment["service"],
            link            = "foo",
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

