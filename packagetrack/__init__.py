"""A simple, generic interface to track packages.

Supported shippers:
    Federal Express, UPS, U.S. Postal Service

Basic usage:

    >>> from packagetrack import Package
    >>> package = Package('1Z9999999999999999')
    # Identify packages (UPS, FedEx, and USPS)
    >>> package.shipper
    'UPS'
    # Track packages (UPS only, requires API access)
    >>> info = package.track()
    >>> print info.status
    IN TRANSIT TO
    >>> print info.delivery_date
    2010-06-25 00:00:00
    >>> print info.last_update
    2010-06-19 00:54:00
    # Get tracking URLs (UPS, FedEx, and USPS)
    >>> print package.url()
    http://wwwapps.ups.com/WebTracking/processInputRequest?TypeOfInquiryNumber=T&InquiryNumber1=1Z9999999999999999

Configuration:

To enable package tracking, you will need to obtain an API account for
each of the services you wish to use, and then make a config file
that looks like:

    [UPS]
    license_number = XXXXXXXXXXXXXXXX
    user_id = XXXX
    password = XXXX

    [FedEx]
    key = XXXXXXXXXXXXXXXX
    password = XXXXXXXXXXXXXXXXXXXXXXXXX
    account_number = #########
    meter_number = #########

    [USPS]
    userid = XXXXXXXXXXXX
    password = XXXXXXXXXXXX


The default location for this file is ~/.packagetrack.

"""
import os.path
import sys

from .service.fedex_interface import FedexInterface
from .service.ups_interface   import UPSInterface
from .service.usps_interface  import USPSInterface

if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


__authors__     = 'Scott Torborg, Michael Stella'
__credits__     = ['Scott Torborg', 'Michael Stella']
__license__     = 'GPL'
__maintainer__  = 'Scott Torborg'
__status__      = 'Development'
__version__     = '0.3.1'

_interfaces = {}

config = ConfigParser()


def register_interface(shipper, interface):
    global _interfaces
    _interfaces[shipper] = interface


def get_interface(shipper):
        if shipper in _interfaces:
            return _interfaces[shipper]
        else:
            raise UnsupportedShipper


register_interface('UPS', UPSInterface())
register_interface('FedEx', FedexInterface())
register_interface('USPS', USPSInterface())


class UnsupportedShipper(Exception):
    pass


class Package(object):
    """A package to be tracked."""

    def __init__(self, tracking_number, configfile=None):
        """
            Options:
                tracking_number - required
                configfile - optional path to a config file, see docs.
        """

        # allow the user to specify an alternate config file
        if not configfile:
            configfile = os.path.expanduser('~/.packagetrack')

        if not os.path.exists(configfile):
            raise IOError("Config file does not exist - create one?")

        config.read([configfile])

        self.tracking_number = tracking_number.upper().replace(' ', '')
        self.shipper = None
        for shipper, iface in _interfaces.items():
            if iface.identify(self.tracking_number):
                self.shipper = shipper
                break

    def track(self):
        """Tracks the package, returning a TrackingInfo object"""

        return get_interface(self.shipper).track(self.tracking_number)

    def url(self):
        """Returns a URL that can be used to go to the shipper's
        tracking website, to track this package."""

        return get_interface(self.shipper).url(self.tracking_number)

    def validate(self):
        """Validates this package's tracking number, returns true or false"""
        return get_interface(self.shipper).validate(self.tracking_number)


def linkify_tracking_number(tracking_number):
    from webhelpers.html.tags import HTML
    try:
        return HTML.a(tracking_number, href=Package(tracking_number).url())
    except UnsupportedShipper:
        return tracking_number
