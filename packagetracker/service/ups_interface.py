
import json
import logging
import requests
from datetime import datetime

from ..data import TrackingInfo
from ..service import BaseInterface, InvalidTrackingNumber, TrackFailed


log = logging.getLogger()


class UPSInterface(BaseInterface):
    click_url = 'http://wwwapps.ups.com/WebTracking/processInputRequest?TypeOfInquiryNumber=T&InquiryNumber1={num}'

    _api_urls = {
        "test":         'https://wwwcie.ups.com/rest/Track',
        "production":   'https://onlinetools.ups.com/rest/Track',
    }

    @property
    def api_url(self):
        if self.testing:
            return self._api_urls['test']
        return self._api_urls['production']


    def identify(self, num):
        """
        Identify a package.

        Args:
            num (str): Tracking number

        Returns:
            bool: true if the given number is a UPS tracking number.
        """
        return num.startswith('1Z') and len(num) == 18


    def validate(self, tracking_number):
        """
        Validate this tracking number.

        Returns:
            bool: True if this is a valid UPS tracking number.
        """

        tracking_num = tracking_number[2:-1]
        odd_total = 0
        even_total = 0

        for ii, digit in enumerate(tracking_num.upper()):
            try:
                value = int(digit)
            except ValueError:
                value = int((ord(digit) - 63) % 10)
            if (ii + 1) % 2:
                odd_total += value
            else:
                even_total += value

        total = odd_total + even_total * 2
        check = ((total - (total % 10) + 10) - total) % 10
        try:
            return (check == int(tracking_number[-1:]))
        except ValueError:
            return False


    def _build_access_request(self):
        return {
            'UsernameToken': {
                'Username': self.config.get('UPS', 'user_id'),
                'Password': self.config.get('UPS', 'password'),
            },
            'AccessLicenseNumber': self.config.get('UPS', 'license_number'),
        }


    def _build_track_request(self, tracking_number):
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
        return {
            'UPSSecurity': self._build_access_request(),
            'TrackRequest': self._build_track_request(tracking_number),
        }


    def _send_request(self, tracking_number):
        body = self._build_request(tracking_number)
        log.debug('Request: {}'.format(json.dumps(body, indent=2)))

        resp = requests.post(self.api_url, data=json.dumps(body))
        log.debug('Response: {}'.format(resp.json()))
        data = resp.json()

        # check for fatal errors now
        if 'Fault' in data:
            raise TrackFailed(data['Fault']['detail']['Errors']['ErrorDetail']['PrimaryErrorCode']['Description'])

        return data


    def _parse_response(self, rsp, tracking_number):
        root = rsp['TrackResponse']

        response = root['Response']
        status_code = int(response['ResponseStatus']['Code'])
        if status_code != 1:
            raise TrackFailed(response['ResponseStatus']['Description'])

        # we need the service code, some things are treated differently
        service_code = root['Shipment']['ShipmentType']['Code']
        service_description = 'UPS %s' % root['Shipment']['Service']['Description']

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
            if status_code == 'M':
                last_location = None

            else:
                # the last known location is interesting
                loc = activity['ActivityLocation']['Address']
                last_location = ','.join((loc['City'],
                                          loc['StateProvinceCode'],
                                          loc['CountryCode']))

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
        )

        # add a single event, UPS doesn't seem to support multiple?

        for e in package['Activity']:
            loc = e['ActivityLocation']['Address']
            location = None
            if 'City' in loc:
                location = ','.join((loc['City'],
                                     loc['StateProvinceCode'],
                                     loc['CountryCode']))

            edate = datetime.strptime(e['Date'], "%Y%m%d").date()
            etime = datetime.strptime(e['Time'], "%H%M%S").time()
            timestamp = datetime.combine(edate, etime)
            trackinfo.addEvent(
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
            raise InvalidTrackingNumber()

        resp = self._send_request(num)
        return self._parse_response(resp, num)

