import unittest
from parameterized import parameterized

from packagetracker import PackageTracker

from .data import FEDEX_TEST_NUMBERS


class TestFedEx(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('FedEx')


    @parameterized.expand(FEDEX_TEST_NUMBERS.keys())
    def test_good_numbers(self, num):
        assert self.interface.identify(num)
        assert self.interface.validate(num)
        p = self.tracker.package(num)
        self.assertEqual(p.shipper, 'fedex')


    def test_fedex_url(self):
        num = '012345678901234'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


#    def test_track_fedex(self):
#        if not self.tracker.config.has_section('FedEx'):
#            return self.skipTest("No FedEx config, skipping tests")
#
#        p = self.tracker.package('012345678901234')
#        try:
#            p.track()
#        except NotImplementedError:
#            pass
#        else:
#            raise AssertionError('tracking fedex package should fail')
