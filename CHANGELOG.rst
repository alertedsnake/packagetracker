Changelog
==================

0.5.0 (alertedsnake):
---------------------

A complete reworking of `packagetrack`_ with the following goals:

* Top-level service interface to allow caching config data and to avoid
  using module-level data
* Reworked the concept of creating a 'package' objects
* HTTP calls now all use `requests`
* Using JSON where available rather than XML
* Improved tracking number validation
* Moved exceptions into their own module
* More implementation of USPS validation - there isn't a lot of documentation for this
* Re-implemented USPS tracking
* Tests now use documented test tracking numbers
* Tests are mostly standardized
* Skip validating UPS test numbers, since they don't actually have valid checksums.  We'll
  have to use a few real numbers to verify this, unfortunately.
* Many, many bugfixes
* Many, many testing bugfixes
* Much more inline documentation
* Sphinx-generated docs
* Python 3.6+ support only.  Feel free to disagree, but go see the `python clock`_.

More to come.


.. _packagetrack: https://github.com/storborg/packagetrack/
.. _python clock: https://pythonclock.org/
