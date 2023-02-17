import datetime
import unittest
from parameterized import parameterized

from packagetracker            import PackageTracker
from packagetracker.exceptions import TrackFailed, InvalidTrackingNumber
from packagetracker.data       import TrackingEvent

from .data import UPS_TEST_NUMBERS, UPS_FAIL_NUMBER, UPS_BOGUS_NUMBER


class TestUPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('UPS')


    def test_ups_url(self):
        num = list(UPS_TEST_NUMBERS.keys())[0]
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    @parameterized.expand(UPS_TEST_NUMBERS.keys())
    def test_good_numbers(self, num):
        assert self.interface.identify(num)
        assert self.interface.validate(num)
        p = self.tracker.package(num)
        self.assertEqual(p.shipper, 'ups')

    def test_bad_number(self):
        assert not self.interface.identify(UPS_BOGUS_NUMBER)
        assert not self.interface.validate(UPS_BOGUS_NUMBER)

        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(UPS_BOGUS_NUMBER)


    def test_track_delivered(self):
        """In which we test a delivered package."""

        num = '1Z12345E0205271688'
        if not self.tracker.config.has_section('UPS'):
            return self.skipTest("No UPS config, skipping tests")

        p = self.tracker.package(num)
        info = p.track()
        print(info)
        self.assertEqual(info.tracking_number, num)
        self.assertEqual(info.status, 'DELIVERED')
        self.assertEqual(info.service, "UPS 2ND DAY AIR")
        #self.assertEqual(info.location, 'ANYTOWN,GA,US')
        self.assertEqual(info.delivery_detail, 'BACK DOOR')
        self.assertIsInstance(info.last_update, datetime.datetime)

        # verify we have a delivered date here
        self.assertIsInstance(info.last_event, TrackingEvent)
        self.assertIsInstance(info.last_event.date, datetime.date)

        # we have no date here now though
        self.assertIsNone(info.delivery_date)


    def test_track_origin_scan(self):
        """
        In which we test a package which has been scanned at the
        origin but not delivered.
        """
        if not self.tracker.config.has_section('UPS'):
            return self.skipTest("No UPS config, skipping tests")

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
            return self.skipTest("No UPS config, skipping tests")

        p = self.tracker.package(UPS_FAIL_NUMBER)
        with self.assertRaises(TrackFailed):
            p.track()


    def test_track_bogus_num(self):
        """In which we test a bogus tracking number."""
        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(UPS_BOGUS_NUMBER)
