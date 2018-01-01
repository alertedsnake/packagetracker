import datetime
import unittest

from packagetracker            import PackageTracker
from packagetracker.exceptions import TrackFailed, InvalidTrackingNumber
from packagetracker.data       import TrackingEvent

# number, description
# taken from the July 11, 2016, UPS Tracking Tracking Web Service Developer Guide, pg. 13
TEST_NUMBERS = {
    '1Z12345E0205271688': '(Signature Availability), 2nd Day Air, Delivered',
    '1Z12345E6605272234': 'World Wide Express, Delivered',
    '1Z12345E0305271640': '(Second Package: 1Z12345E0393657226), Ground, Delivered',
    '1Z12345E1305277940': 'Next Day Air Saver, ORIGIN SCAN',
    '1Z12345E6205277936': 'Day Air Saver, 2nd Delivery attempt',
    '1Z648616E192760718': 'UPS Worldwide Express Freight, Order Process by UPS',
    '1ZWX0692YP40636269': 'UPS SUREPOST, Response for UPS SUREPOST',
}
FAIL_NUMBER = '1Z12345E1505270452'  # No Tracking Information Available
BOGUS_NUM = '1Z12345E020527079'


class TestUPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('UPS')


    def test_ups_url(self):
        num = list(TEST_NUMBERS.keys())[0]
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    def test_identify(self):
        # test all good ones
        for num in TEST_NUMBERS.keys():
            assert self.interface.identify(num)

        # test the bad one
        assert not self.interface.identify(BOGUS_NUM)


    def test_validate_ups(self):
        # test all good ones
        for num in TEST_NUMBERS.keys():
            assert self.interface.validate(num)

        # and the bad one
        assert not self.interface.validate(BOGUS_NUM)


    def test_create_package(self):
        for num in TEST_NUMBERS.keys():
            self.tracker.package(num)

        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(BOGUS_NUM)


    def test_delivered(self):
        """In which we test a delivered package."""

        num = '1Z12345E0205271688'
        if not self.tracker.config.has_section('UPS'):
            return unittest.skip("No UPS config, skipping tests")

        p = self.tracker.package(num)
        info = p.track()
        print(info)
        self.assertEqual(info.tracking_number, num)
        self.assertEqual(info.status, 'DELIVERED')
        self.assertEqual(info.service, "UPS 2ND DAY AIR")
        self.assertEqual(info.location, 'ANYTOWN,GA,US')
        self.assertEqual(info.delivery_detail, 'BACK DOOR')
        self.assertIsInstance(info.last_update, datetime.datetime)

        # verify we have a delivered date here
        self.assertIsInstance(info.last_event, TrackingEvent)
        self.assertIsInstance(info.last_event.date, datetime.date)

        # and that we can get it here too
        self.assertIsInstance(info.delivery_date, datetime.date)


    def test_origin_scan(self):
        """
        In which we test a package which has been scanned at the
        origin but not delivered.
        """
        if not self.tracker.config.has_section('UPS'):
            return unittest.skip("No UPS config, skipping tests")

        num = '1Z12345E1305277940'
        p = self.tracker.package(num)
        info = p.track()
        self.assertEqual(info.tracking_number, num)
        self.assertEqual(info.status, 'ORIGIN SCAN')
        self.assertEqual(info.service, "UPS NEXT DAY AIR SAVER")
        self.assertIsInstance(info.last_update, datetime.datetime)


    def test_track_failed(self):
        """
        In which we test a tracking number which has no
        information available.
        """
        if not self.tracker.config.has_section('UPS'):
            return unittest.skip("No UPS config, skipping tests")

        p = self.tracker.package(FAIL_NUMBER)
        with self.assertRaises(TrackFailed):
            p.track()


    def test_bad_track_num(self):
        """In which we test a bogus tracking number."""
        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(BOGUS_NUM)

