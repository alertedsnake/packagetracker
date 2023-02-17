import unittest
from parameterized import parameterized

from packagetracker            import PackageTracker
from packagetracker.exceptions import InvalidTrackingNumber

from .data import DHL_TEST_NUMBERS, DHL_FAIL_NUMBER, DHL_TEST_FORMATS


class TestDHL(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('DHL')


    def testGood(self):
        if not self.tracker.config.has_section('DHL'):
            return self.skipTest("No DHL config, skipping tests")

        for num, status in DHL_TEST_NUMBERS.items():
            p = self.tracker.package(num, 'DHL')
            result = p.track()

            self.assertEqual(result.status, status)
            self.assertEqual(result.tracking_number, num)
            if status == 'transit':
                self.assertIsNone(result.delivery_date)


    def test_track_failed(self):
        """
        In which we test a tracking number which has no
        information available.
        """
        if not self.tracker.config.has_section('DHL'):
            return self.skipTest("No DHL config, skipping tests")

        p = self.tracker.package(DHL_FAIL_NUMBER, 'DHL')
        with self.assertRaises(InvalidTrackingNumber):
            p.track()


    @parameterized.expand(DHL_TEST_FORMATS)
    def test_good_formats(self, num):
        assert self.interface.identify(num)
        assert self.interface.validate(num)
        p = self.tracker.package(num, 'DHL')
        self.assertTrue(p.validate())
        self.assertEqual(p.shipper, 'dhl')


    def test_bad_format(self):
        p = self.tracker.package("thisisnotanumber", 'DHL')
        self.assertFalse(p.validate())
