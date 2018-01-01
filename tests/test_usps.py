import unittest

from packagetracker import PackageTracker


class TestUSPS(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)

    def test_identify_usps(self):
        test_numbers = (
            '9205596900128506211821',
            '82 000 000 00',
            'EC 000 000 000 US',
        )
        for num in test_numbers:
            assert self.tracker.package(num).shipper == 'USPS'


    def test_usps_url(self):
        num = '9205596900128506211821'
        url = self.tracker.package(num).url()
        assert num in url
        assert url.startswith('http')

    def test_usps_validate(self):
        assert self.tracker.package('9205596900128506211821').validate()
        assert not self.tracker.package('9405503699300451134169').validate()


    def test_track(self):
        if not self.tracker.config.has_section('USPS'):
            return unittest.skip("No USPS config, skipping tests")

        # nope, not yet
        return unittest.skip("not yet implemented")

