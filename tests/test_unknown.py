import unittest

from packagetracker import PackageTracker, UnsupportedShipper, linkify_tracking_number


class TestUnknown(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)


    def linkify_unknown(self):
        num = '123412-412412412-ABC'
        link = linkify_tracking_number(num)
        assert num in link
        assert 'href' not in link


    def test_identify_unknown(self):
        with self.assertRaises(UnsupportedShipper):
            self.tracker.package('14324423523')

