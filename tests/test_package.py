import unittest

from packagetracker import PackageTracker
from packagetracker.exceptions import UnsupportedShipper


class TestPackage(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.tracker = PackageTracker()


    def test_bogus(self):
        # test an invalid shipper name
        with self.assertRaises(UnsupportedShipper):
            self.tracker.package('1234567890', service = 'bogus')
