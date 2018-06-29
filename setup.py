import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), 'r') as f:
        return f.read()


class Tox(TestCommand):

    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


requirements = [
    'fedex',
    'requests',
    'six',
]

setup(
    name                = 'packagetracker',
    version             = '0.5.1',
    author              = "Michael Stella",
    author_email        = "michael@thismetalsky.org",
    license             = "GPL",
    keywords            = "track packages ups fedex usps shipping",
    url                 = "http://github.com/alertedsnake/packagetracker",
    description         = 'Track packages.',
    long_description    = read('README.rst'),
    packages            = find_packages(),
    python_requires = '>=3.6',
    install_requires    = requirements,
    tests_require       = requirements + [
        'nose',
        'tox',
        'virtualenv',
    ],
    cmdclass            = {'test': Tox},
    test_suite          = 'nose.collector',
    zip_safe            = False,
    classifiers         = [
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Programming Language :: Python"
          "Programming Language :: Python :: 3 :: Only",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
    ]
)

