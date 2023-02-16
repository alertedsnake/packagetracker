import unittest

from packagetracker            import PackageTracker
from packagetracker.exceptions import InvalidTrackingNumber

TEST_NUMBERS = {
    '7777777770': 'transit',
}

FAIL_NUMBER = '7777777771'


class TestDHL(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('DHL')


    def testGood(self):
        if not self.tracker.config.has_section('DHL'):
            return self.skipTest("No DHL config, skipping tests")

        for num, status in TEST_NUMBERS.items():
            p = self.tracker.package(num)
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

        p = self.tracker.package(FAIL_NUMBER)
        with self.assertRaises(InvalidTrackingNumber):
            p.track()
