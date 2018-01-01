import datetime
import unittest

from packagetracker.data import TrackingInfo, DATE_FORMAT


class TestTrackingInfo(unittest.TestCase):

    def test_repr(self):
        now = datetime.datetime.now()
        today = datetime.date.today()
        info = TrackingInfo(tracking_number='1Z9999999999999999',
                            delivery_date=today,
                            status='IN TRANSIT',
                            last_update=now)
        s = repr(info)
        assert now.strftime(DATE_FORMAT) in s
        assert str(today) in s
        assert 'IN TRANSIT' in s

