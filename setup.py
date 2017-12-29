import os
import packagetrack
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), 'r') as f:
        return f.read()


setup(name='packagetrack',
      version=packagetrack.__version__,
      author="Scott Torborg",
      author_email="storborg@mit.edu",
      license="GPL",
      keywords="track packages ups fedex usps shipping",
      url="http://github.com/storborg/packagetrack",
      description='Track packages.',
      packages=find_packages(exclude=['tests']),
      install_requires=[
          'fedex'
      ],
      long_description=read('README.rst'),
      test_suite='nose.collector',
      zip_safe=False,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Intended Audience :: Developers",
          "Natural Language :: English",
          "Programming Language :: Python"])
