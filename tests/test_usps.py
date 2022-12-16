import datetime
import pytest
import unittest

from packagetracker            import PackageTracker
from packagetracker.exceptions import TrackFailed, InvalidTrackingNumber

TEST_NUMBERS = {
    '9400100000000000000000':               'USPS Tracking',
    '9205500000000000000000':               'Priority Mail',
    '82 000 000 00':                        'Global Express Guaranteed',
    'EC 000 000 000 US':                    'Priority Mail International',
}
BOGUS_NUM = '9405503699300451134169'
REAL_PACKAGES = [
    'LM181476342CA',
]

class TestUSPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('USPS')


    def test_usps_url(self):
        num = '9205596900128506211821'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    def test_identify(self):
        for num in TEST_NUMBERS.keys():
            print("Tracking %s", num)
            assert self.interface.identify(num)


    @pytest.mark.skip(reason="no valid numbers")
    def test_validate(self):
        for num in TEST_NUMBERS.keys():
            print("Validating %s", num)
            assert self.interface.validate(num)

        # this is a bad one
        assert not self.interface.validate(BOGUS_NUM)


    def test_create_package(self):
        for num in TEST_NUMBERS.keys():
            self.tracker.package(num)

        with self.assertRaises(InvalidTrackingNumber):
            self.interface.track(BOGUS_NUM)


    @pytest.mark.skip(reason="no valid numbers")
    def test_track_delivered(self):
        """
        In which we track a real package.
        """
        if not self.tracker.config.has_section('USPS'):
            return self.skipTest("No USPS config, skipping tests")

        num = REAL_PACKAGES[0]
        p = self.tracker.package(num)
        info = p.track()
        self.assertEqual(info.tracking_number, num)
        self.assertEqual(info.status, 'Delivered')
        self.assertIsInstance(info.delivery_date, datetime.date)

        # this package actually has 14 events
        self.assertTrue(len(info.events) > 1)


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

        num = '7196901075600307738501'
        with self.assertRaises(InvalidTrackingNumber):
            p = self.tracker.package(num)
            p.track()
