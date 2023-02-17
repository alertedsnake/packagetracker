import datetime
import pytest
import unittest
from parameterized import parameterized

from packagetracker            import PackageTracker
from packagetracker.exceptions import TrackFailed, InvalidTrackingNumber

from .data import USPS_TEST_NUMBERS, USPS_BOGUS_NUM, USPS_REAL_PACKAGES


class TestUSPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('USPS')


    def test_usps_url(self):
        num = '9205596900128506211821'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    @parameterized.expand(USPS_TEST_NUMBERS.keys())
    def test_good_numbers(self, num):
        print(f"Tracking {num}")
        p = self.tracker.package(num)
        p.validate()
        self.assertEqual(p.shipper, 'usps')


    def test_bogus_numbers(self):
        # this is a bad one
        assert not self.interface.validate(USPS_BOGUS_NUM)

        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(USPS_BOGUS_NUM)


    @pytest.mark.skip(reason="no valid numbers")
    def test_track_delivered(self):
        """
        In which we track a real package.
        """
        if not self.tracker.config.has_section('USPS'):
            return self.skipTest("No USPS config, skipping tests")

        num = USPS_REAL_PACKAGES[0]
        p = self.tracker.package(num)
        self.assertEqual(p.shipper, 'usps')
        info = p.track()
        self.assertEqual(info.tracking_number, num)
        self.assertEqual(info.status, 'Delivered')
        self.assertIsInstance(info.delivery_date, datetime.date)

        # this package actually has 14 events
        self.assertTrue(len(info.events) > 1)


    @pytest.mark.skip(reason = "need a number to validate this")
    def test_track_no_information(self):
        """
        In which we test a tracking number for which there is no
        available status information.
        """
        if not self.tracker.config.has_section('USPS'):
            return self.skipTest("No USPS config, skipping tests")

        num = '7196901075600307738508'  # not a real test number!
        with self.assertRaises(TrackFailed):
            p = self.tracker.package(num)
            p.track()


    def test_track_invalid_number(self):
        if not self.tracker.config.has_section('USPS'):
            return self.skipTest("No USPS config, skipping tests")

        num = '9196901075600307738501'
        with self.assertRaises(InvalidTrackingNumber):
            p = self.tracker.package(num)
            self.assertEqual(p.shipper, 'usps')
            p.track()
