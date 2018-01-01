import unittest

from packagetracker import PackageTracker


class TestFedEx(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)


    def test_identify_fedex(self):
        assert self.tracker.package('012345678901234').shipper == 'FedEx'


    def test_fedex_url(self):
        num = '012345678901234'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')


    def test_track_fedex(self):
        if not self.tracker.config.has_section('FedEx'):
            return unittest.skip("No FedEx config, skipping tests")

        p = self.tracker.package('012345678901234')
        try:
            p.track()
        except NotImplementedError:
            pass
        else:
            raise AssertionError('tracking fedex package should fail')


