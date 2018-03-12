#!/usr/bin/env python2

from __future__ import print_function

import argparse
import os
import os.path
import requests


# Disable urllib3 warnings:
# https://github.com/shazow/urllib3/issues/497
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


CERT = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
        'localhost.crt')


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Script to test your micro-service is correctly configured',
    )
    parser.add_argument(
        '-d', '--domain',
        default='localhost',
        help='API domain (defaults to localhost)',
        required=False,
    )
    parser.add_argument(
        '-p', '--port',
        default='5000',
        help='API port (defaults to 5000)',
        required=False,
    )
    parser.add_argument(
        '-c', '--cert-path',
        default=CERT,
        help='Path to self signed certificate (defaults to localhost.crt)',
        required=False,
    )
    args = parser.parse_args()

    if not os.path.exists(args.cert_path):
        raise Exception('No Certificate File Found at {}'.format(args.cert_path))

    BASE_URL = 'https://{}:{}'.format(args.domain, args.port)

    # POST the message 'foo'
    DIGEST = '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'
    url = '{}/messages/{}'.format(BASE_URL, DIGEST)
    r = requests.delete(url=url, verify=args.cert_path)
    print(r.status_code)
    print("{}".format(r.json()))

    DIGEST= 'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9'
    url = '{}/messages/{}'.format(BASE_URL, DIGEST)
    r = requests.delete(url=url, verify=args.cert_path)
    print(r.status_code)
    print("{}".format(r.json()))

if __name__ == '__main__':
    main()
