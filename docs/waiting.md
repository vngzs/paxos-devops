[➥ back to readme](../README.md)

## Waiting

### Why

When called with the `-d` flag, `docker-compose` tries to daemonize itself.
This means if you try to run the test suite exactly as described, you will
probably see errors because the `docker-compose` process forks before the
service is fully initialized:

```console
$ docker-compose up -d && ./devops-test-script/test.py --domain localhost --port 5000 --cert-path ./localhost.crt
Creating network "sha256py_default" with the default driver
Creating sha256py_web_1 ... done
Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 601, in urlopen
    chunked=chunked)
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 346, in _make_request
    self._validate_conn(conn)
  File "/usr/lib/python3.6/site-packages/urllib3/connectionpool.py", line 850, in _validate_conn
    conn.connect()
  File "/usr/lib/python3.6/site-packages/urllib3/connection.py", line 326, in connect
    ssl_context=context)
  File "/usr/lib/python3.6/site-packages/urllib3/util/ssl_.py", line 329, in ssl_wrap_socket
    return context.wrap_socket(sock, server_hostname=server_hostname)
  File "/usr/lib/python3.6/ssl.py", line 407, in wrap_socket
    _context=self, _session=session)
  File "/usr/lib/python3.6/ssl.py", line 814, in __init__
    self.do_handshake()
  File "/usr/lib/python3.6/ssl.py", line 1068, in do_handshake
    self._sslobj.do_handshake()
  File "/usr/lib/python3.6/ssl.py", line 689, in do_handshake
    self._sslobj.do_handshake()
OSError: [Errno 0] Error
...
```

### `ensure_up.sh`

I created the [`ensure_up.sh`](../scripts/ensure_up.sh) script to check if the service is fully online:

```console
$ ./scripts/ensure_up.sh -h
usage: ./scripts/ensure_up.sh [-d DOMAIN] [-p PORT] [-c CAFILE] [-r RETRIES] [-D] [-O] [-P] [-N] [-B]"

Test TLS connection to sha256py docker container to ensure the web service is running.
Tries tests in this order: openssl, python2, ncat, bash.

Any pass will result in zero exit status, any failure will result in nonzero.

optional arguments:
  -d DOMAIN   domain to connect to (default: localhost)
  -p PORT     port to connect to (default: 5000)
  -c CAFILE   certificate file (default: localhost.crt)
  -r RETRIES  number of times to retry a connection (default: 5)
  -D          debug
  -O          force test a connection to service using openssl (best, default)
  -P          force test a connection to service using python2
  -N          force test a connection to service using ncat
  -B          force test a connection to service using bash
  -h          show this help text
```

This script essentially just waits for an SSL connection on the default (or
specified) host and port with the supplied
[`localhost.crt`](../localhost.crt)
to be listening. It
retries a couple of times (5 retries, 1 second apart by default). It tries to
be portable by supplying multiple means of checking if the service is online,
and automatically detecting the best one which is available to you.

See it in action here:

```console
$ docker-compose up -d && ./scripts/ensure_up.sh && ./devops-test-script/test.py -c ./localhost.crt
Creating network "sha256py_default" with the default driver
Creating sha256py_web_1 ... done
https://localhost:5000/messages/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa correctly not found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 correctly found
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found

***************************************************************************
All tests passed!
***************************************************************************
```

### Manually checking

You can achieve the same thing with `openssl` if you have that installed:

```console
$ docker-compose up -d && WAIT=0; until echo -n | openssl s_client -connect localhost:5000 &>/dev/null || [[ ${WAIT} -eq 3 ]]; do sleep $((WAIT++)); done; [[ $WAIT -lt 3 ]] && ./devops-test-script/test.py -c ./localhost.crt
Creating network "sha256py_default" with the default driver
Creating sha256py_web_1 ... done
https://localhost:5000/messages/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa correctly not found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 correctly found
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found

***************************************************************************
All tests passed!
***************************************************************************
```

#### [`ensure_up.py`](../scripts/ensure_up.py)

Or with the [`ensure_up.py`](../scripts/ensure_up.py) script provided, as long
as you have [Python 2.7](./requirements.md):

```console
$ docker-compose up -d && ./scripts/check_up.py && ./devops-test-script/test.py -c ./localhost.crt
Creating network "sha256py_default" with the default driver
Creating sha256py_web_1 ... done
https://localhost:5000/messages/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa correctly not found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 correctly found
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found

***************************************************************************
All tests passed!
***************************************************************************
```

