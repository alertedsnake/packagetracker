"""A simple, generic interface to track packages.

Supported shippers currently include: FedEx, UPS, U.S. Postal Service.

Basic usage
***********

    >>> from packagetracker import PackageTracker
    >>> tracker = PackageTracker()
    >>> package = tracker.package('1Z9999999999999999')
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

Configuration
*************

To enable package tracking, you will need to obtain an API account for
each of the services you wish to use, and then make a config file
that looks like::

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


The default location for this file is ~/.config/packagetrack.

"""
import logging
import os.path
from pkg_resources            import get_distribution, DistributionNotFound
from six.moves.configparser   import ConfigParser

from .service.fedex_interface import FedexInterface
from .service.ups_interface   import UPSInterface
from .service.usps_interface  import USPSInterface
from .exceptions              import (InvalidTrackingNumber,
                                      UnsupportedShipper,
                                      TrackFailed)

__all__         = ['InvalidTrackingNumber',
                   'UnsupportedShipper',
                   'TrackFailed']

__authors__     = 'Michael Stella'
__license__     = 'GPL'
__maintainer__  = 'Michael Stella'
__status__      = 'Development'

try:
    __version__ = get_distribution('packagetracker').version
except DistributionNotFound:
    __version__ = '0.1.0.dev1'

log = logging.getLogger()



class PackageTracker(object):
    """
    The main package tracking interface object.

    Args:
        config_file (str): path to a valid config file
        testing (bool): True to enable test-only mode.
    """

    def __init__(self, config_file='~/.config/packagetrack', testing=False):
        self.config_file = os.path.expanduser(config_file)
        self.testing = testing

        if not os.path.exists(self.config_file):
            raise IOError("Config file does not exist - create one?")

        # read the config file
        self.config = ConfigParser()
        self.config.read(self.config_file)

        # register the interfaces
        self._interfaces = {}
        self.register_interface('UPS', UPSInterface(config=self.config, testing=testing))
        self.register_interface('USPS', USPSInterface(config=self.config, testing=testing))
        self.register_interface('FedEx', FedexInterface(config=self.config, testing=testing))


    def register_interface(self, shipper, interface):
        """
        Args:
            shipper (str): Shipper short name
            interface (obj): subclass of BaseInterface
        """

        log.debug("Registered interface {}".format(shipper))
        self._interfaces[shipper] = interface


    def package(self, tracking_number):
        """
        Returns a Package object given the tracking number.

        Args:
            tracking_number (str)

        Returns:
            Package
        """

        return Package(self, tracking_number)


    @property
    def interfaces(self):
        return self._interfaces.items()

    def interface(self, key):
        return self._interfaces.get(key)


class Package(object):
    """
    A package to be tracked.

    Most likely you won't use this directly, you'll create a Package
    object by calling PackageTracker.package() instead.

    Args:
        parent (PackageTracker): an instance of PackageTracker
        tracking_number (str): the tracking number

    """

    def __init__(self, parent, tracking_number):
        self.tracking_number = tracking_number.upper().replace(' ', '')
        self.shipper = None
        self.iface = None

        for shipper, iface in parent.interfaces:
            log.debug("{}: Testing shipper {}".format(tracking_number, shipper))

            if iface.identify(self.tracking_number):
                self.shipper = shipper
                self.iface = iface
                break

        if not self.iface or not self.shipper:
            raise UnsupportedShipper()

        log.debug("{}: shipper is {}".format(tracking_number, self.shipper))


    def track(self):
        """Tracks the package, returning a TrackingInfo object"""
        return self.iface.track(self.tracking_number)


    def url(self):
        """Returns a URL that can be used to go to the shipper's
        tracking website, to track this package."""
        return self.iface.url(self.tracking_number)


    def validate(self):
        """Validates this package's tracking number, returns true or false"""
        return self.iface.validate(self.tracking_number)


def linkify_tracking_number(tracking_number):
    from webhelpers.html.tags import HTML
    try:
        return HTML.a(tracking_number, href=Package(tracking_number).url())
    except UnsupportedShipper:
        return tracking_number
