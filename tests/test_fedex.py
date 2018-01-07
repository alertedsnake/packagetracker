import unittest

from packagetracker            import PackageTracker
#from packagetracker.exceptions import TrackFailed, InvalidTrackingNumber, UnsupportedShipper


TEST_NUMBERS = {
    '449044304137821': 'Shipment information sent to FedEx',
    '149331877648230': 'Tendered',
    '020207021381215': 'Picked Up',
    '403934084723025': 'Arrived at FedEx location',
    '920241085725456': 'At local FedEx facility',
    '568838414941':     'At destination sort facility',
    '039813852990618': 'Departed FedEx location',
    '231300687629630': 'On FedEx vehicle for delivery',
    '797806677146':     'International shipment release',
    '377101283611590': 'Customer not available or business closed',
    '852426136339213': 'Local Delivery Restriction',
    '797615467620':     'Incorrect Address',
    '957794015041323': 'Unable to Deliver',
    '076288115212522': 'Returned to Sender/Shipper',
    '581190049992':     'International Clearance delay',
    '122816215025810': 'Delivered',
    '843119172384577': 'Hold at Location',
    '070358180009382': 'Shipment Canceled',
}


class TestFedEx(unittest.TestCase):

    def setUp(self):
        self.tracker = PackageTracker(testing=True)
        self.interface = self.tracker.interface('FedEx')


    def test_identify(self):
        # test all good ones
        for num in TEST_NUMBERS.keys():
            assert self.interface.identify(num)


    def test_validate(self):
        # test all good ones
        for num in TEST_NUMBERS.keys():
            assert self.interface.validate(num)


    def test_create_package(self):
        for num in TEST_NUMBERS.keys():
            self.tracker.package(num)


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


