import urllib
from datetime import datetime, date, time

import packagetrack
from ..xml_dict import dict_to_xml, xml_to_dict
from ..data import TrackingInfo
from ..service import BaseInterface, TrackFailed, InvalidTrackingNumber

class UPSInterface(BaseInterface):
    api_url = 'https://wwwcie.ups.com/ups.app/xml/Track'

    def __init__(self):
        self.attrs = {'xml:lang': 'en-US'}

    def identify(self, tracking_number):
        return tracking_number.startswith('1Z')

    def validate(self, tracking_number):
        "Return True if this is a valid UPS tracking number."
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
        config = packagetrack.config
        d = {
            'AccessRequest': {
                'AccessLicenseNumber': config.get('UPS', 'license_number'),
                'UserId': config.get('UPS', 'user_id'),
                'Password': config.get('UPS', 'password')
            }
        }
        return dict_to_xml(d, self.attrs)

    def _build_track_request(self, tracking_number):
        req = {
            'TransactionReference': {
                'RequestAction': 'Track',
            },
            'RequestOption': '1',
        }
        d = {
            'TrackRequest': {
                'Request': req,
                'TrackingNumber': tracking_number
            }
        }
        return dict_to_xml(d)

    def _build_request(self, tracking_number):
        return (self._build_access_request() +
                self._build_track_request(tracking_number))

    def _send_request(self, tracking_number):
        body = self._build_request(tracking_number)
        webf = urllib.urlopen(self.api_url, body)
        resp = webf.read()
        webf.close()
        return resp

    def _parse_response(self, raw, tracking_number):
        root = xml_to_dict(raw)['TrackResponse']

        response = root['Response']
        status_code = response['ResponseStatusCode']
        status_description = response['ResponseStatusDescription']
        # Check status code?

        # we need the service code, some things are treated differently
        service_code = root['Shipment']['Service']['Code']
        service_description = 'UPS %s' % root['Shipment']['Service']['Description']

        package = root['Shipment']['Package']

        # make activites a list if it's not already
        if type(package['Activity']) != list:
            package['Activity'] = [package['Activity']]

        # this is the last activity, the one we get status info from
        activity = package['Activity'][0]

        # here's the status code, inside the Activity block
        status = activity['Status']['StatusType']['Description']
        status_code = activity['Status']['StatusType']['Code']

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
            location=None
            if 'City' in loc:
                location = ','.join((loc['City'],
                                     loc['StateProvinceCode'],
                                     loc['CountryCode']))

            edate = datetime.strptime(e['Date'], "%Y%m%d").date()
            etime = datetime.strptime(e['Time'], "%H%M%S").time()
            timestamp = datetime.combine(edate, etime)
            trackinfo.addEvent(
                location = location,
                detail = e['Status']['StatusType']['Description'],
                date = timestamp,
            )


        return trackinfo

    def track(self, tracking_number):
        "Track a UPS package by number. Returns just a delivery date."

        if not self.validate(tracking_number):
            raise InvalidTrackingNumber()

        resp = self._send_request(tracking_number)
        return self._parse_response(resp, tracking_number)

    def url(self, tracking_number):
        "Return a tracking info detail URL by number."
        return ('http://wwwapps.ups.com/WebTracking/processInputRequest?'
                'TypeOfInquiryNumber=T&InquiryNumber1=%s' % tracking_number)
