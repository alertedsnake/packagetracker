Changelog
==================

0.7.0a1 (alertedsnake)
----------------------

* Implemented DHL tracking
* Fixed USPS identification to make it stricter
* switched to using parameterized for test cases
* moved test data into its own file
* confirming package identification in tests

0.6.1 (alertedsnake)
--------------------

* Switching to an actually-maintained version of ``python-fedex``

0.6.0 (alertedsnake)
--------------------

* Add type hints
* Return information web link for each package - currently using hardcoded
  links, which are probably not stable.
* Allow for USPS results with no date or time, not sure why this happens.
* Switch to pyproject.toml

0.5.1 (alertedsnake)
--------------------

* Bugfix typo in date handling
* Bugfix location handling in UPS 'M' or 'P' types, which have no location
* Remove some old Python2.7 stuff

0.5.0 (alertedsnake)
--------------------

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
