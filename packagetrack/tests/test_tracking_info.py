from datetime import datetime, date
from unittest import TestCase

from packagetrack.data import TrackingInfo, DATE_FORMAT


class TestTrackingInfo(TestCase):

    def test_repr(self):
        now = datetime.now()
        today = date.today()
        info = TrackingInfo(tracking_number='1Z9999999999999999',
                            delivery_date=today,
                            status='IN TRANSIT',
                            last_update=now)
        s = repr(info)
        assert now.strftime(DATE_FORMAT) in s
        assert str(today) in s
        assert 'IN TRANSIT' in s

