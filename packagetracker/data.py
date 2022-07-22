import datetime
import typing

DATE_FORMAT = "%Y-%m-%d %H:%M"


class TrackingInfo(dict):
    """
    Generic tracking information object returned by a tracking request

    Args:
        tracking_number:    the carrier tracking number
        delivery_date:      date the item was delivered, None if not yet delivered
        status:             last available status
        last_update:        timestamp of the last update
        location:           location of the last update
        delivery_datail:    details about the delivery
        service:            description of the carrier's service used
        link:               a link to the carrier's detail page
    """

    def __init__(self,
                 tracking_number:   str,
                 delivery_date:     datetime.datetime,
                 status:            str,
                 last_update:       datetime.datetime,
                 location:          typing.Optional[str] = None,
                 delivery_detail:   typing.Optional[str] = None,
                 service:           typing.Optional[str] = None,
                 link:              typing.Optional[str] = None):

        self.events = []

        self.tracking_number = tracking_number
        self._delivery_date = delivery_date
        self.status = status
        self.last_update = last_update
        self.link = link

        # last known location
        self.location = location

        # if delivered, how so?
        self.delivery_detail = delivery_detail

        # service type, i.e. FedEx Ground, UPS Basic, etc.
        self.service = service


    def __repr__(self):
        ddate = ldate = None
        if self.delivery_date:
            ddate = self.delivery_date.strftime(DATE_FORMAT)
        if self.last_update:
            ldate = self.last_update.strftime(DATE_FORMAT)

        # return slightly different info if it's delivered
        if self.status == 'DELIVERED':
            return ('<TrackingInfo(service=%r, num=%r, delivery_date=%r, status=%r, location=%r, detail=%r)>' %
                    (
                        self.service,
                        self.tracking_number,
                        ddate,
                        self.status,
                        self.location,
                        self.delivery_detail,
                    ))
        else:
            return ('<TrackingInfo(service=%r, num=%r, delivery_date=%r, status=%r, last_update=%r, location=%r)>' %
                    (
                        self.service,
                        self.tracking_number,
                        ddate,
                        self.status,
                        ldate,
                        self.location,
                    ))


    def add_event(self, date, location, detail):
        """
        Add an event.

        Args:
            date (datetime.datetime): event timestamp
            location (str): location text
            detail (str): event detail

        Returns:
            TrackingEvent: the event added
        """
        e = TrackingEvent(date, location, detail)
        self.events.append(e)
        return e


    @property
    def last_event(self):
        """
        Returns:
            TrackingEvent: the most recent event.
        """
        if self.events:
            return sorted(self.events, key=lambda event: event.date, reverse=True)[0]


    @property
    def delivery_date(self):
        """
        The delivered date, which may be on the last event rather than
        stored in this object itself.

        Returns:
            datetime.datetime
        """
        if self._delivery_date:
            return self._delivery_date
        if self.last_event:
            return self.last_event.date


class TrackingEvent(dict):
    """An individual tracking event, i.e. a status change"""

    def __init__(self, date, location, detail):
        self.date = date
        self.location = location
        self.detail = detail


    def __repr__(self):
        return ('<TrackingEvent(date=%r, location=%r, detail=%r)>' %
                (self.date.strftime("%Y-%m-%d %H:%M"), self.location, self.detail))

