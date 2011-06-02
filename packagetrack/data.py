
class TrackingInfo(dict):
    """Generic tracking information object returned by a tracking request"""

    def __init__(self, tracking_number, delivery_date, status, last_update, location=None, delivery_detail=None, service=None):

        self.events = []

        self.tracking_number = tracking_number
        self.delivery_date = delivery_date
        self.status = status
        self.last_update = last_update

        # last known location
        self.location = location

        # if delivered, how so?
        self.delivery_detail = delivery_detail

        # service type, i.e. FedEx Ground, UPS Basic, etc.
        self.service = service

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, val):
        self[name] = val

    def __repr__(self):
        # return slightly different info if it's delivered
        if self.status == 'DELIVERED':
            return ('<TrackingInfo(svc=%r, delivery_date=%r, status=%r, location=%r, detail=%r)>' %
                        (
                            self.service,
                            self.delivery_date.strftime("%Y-%m-%d %H:%M"),
                            self.status,
                            self.location,
                            self.delivery_detail,
                        )
                    )
        else:
            ddate = None
            if self.delivery_date:
                ddate = self.delivery_date.strftime("%Y-%m-%d %H:%M")

            return ('<TrackingInfo(svc=%r, delivery_date=%r, status=%r, last_update=%r, location=%r)>' %
                        (
                            self.service,
                            ddate,
                            self.status,
                            self.last_update.strftime("%Y-%m-%d %H:%M"),
                            self.location,
                        )
                    )


    def addEvent(self, date, location, detail):
        e = TrackingEvent(date, location, detail)
        self.events.append(e)
        return e


class TrackingEvent(dict):
    """An individual tracking event, i.e. a status change"""

    def __init__(self, date, location, detail):
        self.date = date
        self.location = location
        self.detail = detail

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, val):
        self[name] = val

    def __repr__(self):
        return ('<TrackingEvent(date=%r, location=%r, detail=%r)>' %
                    (self.date.strftime("%Y-%m-%d %H:%M"), self.location, self.detail))

