
class TrackingInfo(object):
    """Generic tracking information object returned by a tracking request"""

    def __init__(self, delivery_date, status, last_update, location=None, delivery_detail=None):
        self.delivery_date = delivery_date
        self.status = status
        self.last_update = last_update

        # last known location
        self.location = location

        # if delivered, how so?
        self.delivery_detail = delivery_detail


    def __repr__(self):
        # return slightly different info if it's delivered
        if self.status == 'DELIVERED':
            return ('<TrackingInfo(delivery_date=%r, status=%r, location=%r, detail=%r)>' %
                        (
                            self.delivery_date.strftime("%Y-%m-%d %H:%M"),
                            self.status,
                            self.location,
                            self.delivery_detail,
                        )
                    )
        else:
            return ('<TrackingInfo(delivery_date=%r, status=%r, last_update=%r, location=%r)>' %
                        (
                            self.delivery_date.strftime("%Y-%m-%d %H:%M"),
                            self.status,
                            self.last_update.strftime("%Y-%m-%d %H:%M"),
                            self.location,
                        )
                    )
