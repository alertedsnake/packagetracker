
import argparse
import logging
from packagetracker import PackageTracker


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--service")
    parser.add_argument("--guess", action = 'store_true')
    parser.add_argument("--debug", action = 'store_true')
    parser.add_argument("tracknum")

    opts = parser.parse_args()

    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    tracker = PackageTracker()
    p = tracker.package(opts.tracknum, service = opts.service, guess = opts.guess)
    info = p.track()
    print(info)
