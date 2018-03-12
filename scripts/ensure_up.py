#!/usr/bin/env python2

from __future__ import print_function

import sys
if __name__ == '__main__' \
	and len(sys.argv) > 1 \
	and sys.argv[1] == 'SUPPORTED?':
    # We're checking the Python version for support.
    v = sys.version_info
    if v[0] < 2 or (v[0] == 2 and v[1] < 7):
        print('Need at least Python 2.7')
        sys.exit(-127)
    else:
        sys.exit(0)

import argparse
import os.path
import socket
import itertools
import ssl
import time

CERT = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                    '..', 'cert.pem')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cert', default=CERT, type=str,
            help='path to certificate')
    parser.add_argument('-p', '--port', default=5000, type=int,
            help='port to attempt connection')
    parser.add_argument('-d', '--domain', default='localhost', type=str,
            help='domain to attempt connection')
    parser.add_argument('-r', '--retries', default=5, type=int,
            help='number of attempts to make')
    parser.add_argument('-s', '--skip', default=False, action='store_true',
            help='skip SSL certificate verification')
    parser.add_argument('-D', '--debug', default=False, action='store_true',
            help='print debug information to standard error')
    args = parser.parse_args()

    def get_debug(should_debug):
        def f(*args, **kwargs):
            if should_debug:
                default_kwargs = {'file': sys.stderr}
                kwargs = dict(itertools.chain(default_kwargs.items(),
                                               kwargs.items()))
                print(*args, **kwargs)
        return f

    debug = get_debug(args.debug)
    debug('checking ... ', end='')
    
    def connect():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if args.skip:
            debug('skipping certificate requirement')
            cert_reqs = ssl.CERT_NONE
            ssl_sock = ssl.wrap_socket(s, cert_reqs=cert_reqs)
        else:
            debug('requiring certificate {}'.format(args.cert))
            cert_reqs = ssl.CERT_REQUIRED
            ssl_sock = ssl.wrap_socket(s, ca_certs=args.cert,
                                    cert_reqs=cert_reqs)
        ssl_sock.connect((args.domain, args.port))

    count = 0
    while count < args.retries:
        try:
            connect()
            debug('success!')
            sys.exit(0)
        except socket.error:
            count += 1
            time.sleep(1)
    debug('tried too many times!')
    sys.exit(1)


if __name__ == '__main__':
    main()
