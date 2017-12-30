import logging
from datetime import datetime, date
from unittest import TestCase
from nose.plugins.skip import SkipTest

from packagetrack import PackageTracker, UnsupportedShipper, linkify_tracking_number

logging.basicConfig(level=logging.DEBUG)


class TestUPS(TestCase):

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
            raise SkipTest

        # This is just a random tracking number found on google. To find more,
        # google for something like:
        # ["Tracking Detail" site:wwwapps.ups.com inurl:WebTracking]
        p = self.tracker.package('1Z58R4770350434926')
        info = p.track()
        assert info.status != ''
        assert isinstance(info.delivery_date, date)
        assert isinstance(info.last_update, datetime)


    def test_validate_ups(self):
        assert self.tracker.package('1Z58R4770350889570').validate()
        assert not self.tracker.package('1Z58R4770350889572').validate()


class TestFedEx(TestCase):

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
            raise SkipTest

        p = self.tracker.package('012345678901234')
        try:
            p.track()
        except NotImplementedError:
            pass
        else:
            raise AssertionError('tracking fedex package should fail')


class TestUSPS(TestCase):

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
            raise SkipTest

        # nope, not yet
        raise SkipTest


    def linkify_ups(self):
        num = '1Z9999999999999999'
        link = linkify_tracking_number(num)
        assert 'href' in link
        assert num in link


class TestUnknown(TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)

    def linkify_unknown(self):
        num = '123412-412412412-ABC'
        link = linkify_tracking_number(num)
        assert num in link
        assert 'href' not in link

    def test_identify_unknown(self):
        assert self.tracker.package('14324423523').shipper is None

    def test_track_unknown(self):
        try:
            self.tracker.package('12391241248').track()
        except UnsupportedShipper:
            pass
        else:
            raise AssertionError("tracking package with unknown "
                                 "shipper should fail")
