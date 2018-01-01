import datetime
import unittest

from packagetracker import PackageTracker


class TestUPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)


    def test_identify_ups(self):
        assert self.tracker.package('1Z9999999999999999').shipper == 'UPS'


    def test_ups_url(self):
        num = '1Z9999999999999999'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    def test_track_ups(self):
        if not self.tracker.config.has_section('UPS'):
            return unittest.skip("No UPS config, skipping tests")

        # This is just a random tracking number found on google. To find more,
        # google for something like:
        # ["Tracking Detail" site:wwwapps.ups.com inurl:WebTracking]
        p = self.tracker.package('1Z58R4770350434926')
        info = p.track()
        assert info.status != ''
        assert isinstance(info.delivery_date, datetime.date)
        assert isinstance(info.last_update, datetime.datetime)


    def test_validate_ups(self):
        assert self.tracker.package('1Z58R4770350889570').validate()
        assert not self.tracker.package('1Z58R4770350889572').validate()


