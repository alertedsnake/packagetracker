packagetracker - Track packages
===============================

:Authors:
    Michael Stella (alertedsnake)

:Version: 0.6.1

This library tracks packages.


Credits
============

Much of this library is based on `packagetrack`_ initially by Scott Torborg.


Installation
============

This package is not published to PyPi, so grab the source and do ``pip install .`` in this directory, or use ``setup.py``.

Example
=======

>>> import packagetracker
>>> tracker = packagetracker.PackageTracker()
>>> package = tracker.package('1Z9999999999999999')
# Identify packages:
>>> package.shipper
'UPS'
# Track packages:
>>> info = package.track()
>>> print info.status
IN TRANSIT TO
>>> print info.delivery_date
2010-06-25 00:00:00
>>> print info.last_update
2010-06-19 00:54:00
# Get tracking URLs (UPS, FedEx, and USPS):
>>> print package.url()
http://wwwapps.ups.com/WebTracking/processInputRequest?TypeOfInquiryNumber=T&InquiryNumber1=1Z9999999999999999


API Configuration
=====================

To enable package tracking, get an account for each of the services you wish
to use, and then make a file at ~/.config/packagetrack that looks like::

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


For USPS, the optional argument 'server' can be set to 'test' or 'production'.

Status
=======

Currently the UPS, USPS, and FedEx interfaces work... mostly well.  I'm sure
there are weird edge cases everywhere, there's a lot of documentation to read,
not all of it good.

License
=======

Packagetrack is released under the GNU General Public License (GPL). See the
LICENSE file for full text of the license.


.. _packagetrack: https://github.com/storborg/packagetrack
.. _python-fedex: https://github.com/python-fedex-devs/python-fedex
.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround tw=80
