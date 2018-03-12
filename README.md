# SHA256py

Solution to the
[Pax Code Challenge](https://www.dropbox.com/s/lyy5btonatq09wx/DevOps%20Engineer.pdf?dl=0).
This repository provides a Docker container for running the sha256sum messages
service.

## Contents

1. [Requirements](./docs/requirements.md#requirements)
   1. [Optional dependencies](./docs/requirements.md#optional-dependencies)
1. [ReST API](#rest-api)
1. [Building and running the image](#building-and-running-the-image)
1. [Stopping the image](#stopping-the-image)
1. [Logs](#logs)
   1. [Captured logs](#captured-logs)
1. [Running tests](#running-tests)
   1. [Waiting for the container to start](#waiting-for-the-container-to-start)
      1. [Waiting](./docs/waiting.md#waiting)
         1. [Why](./docs/waiting.md#why)
         1. [`ensure_up.sh`](./docs/waiting.md#ensure_upsh)
         1. [Manually checking](./docs/waiting.md#manually-checking )
         1. [`ensure_up.py`](./docs/waiting.md#ensure_uppy)
   1. [Cleaning up](#cleaning-up)
1. [Scaling](./docs/scaling.md#scaling)

## Requirements

See [`requirements.md`](./docs/requirements.md)

## ReST API

1. `/messages` takes a message as a JSON POST request in the format
   `{"message": "MESSAGE"}` and returns a hex-formatted sha256 hash digest
   of the message key. It sends HTTP `201` when a message is created and `200`
   if the message already exists.
2. `/messages/<hash>` responds to GET requests and returns the message that
   hashes to `hash`. Nonexistent messages receive a HTTP 404 error.
3. `/messages/<hash>` also responds to DELETE requests, so that messages can be
   cleaned up from the server. Since the service uses Docker volumes to persist
   messages across service restarts, this provides a convenient way to reset
   the container state.

## Building and running the image

From within this directory, run the following command:

```console
$ docker-compose up --build -d
```

## Stopping the image

```console
$ docker-compose down
```

## Logs

You can view the logs by running `docker-compose logs -f` while in this
directory.

### Captured logs

By default, docker stores persistent logs in
`/var/lib/docker/container/${containerid}/${containerid}-json.log`.
You can find the value of `${containerid}` by running

```console
$ docker ps --format '{{.ID}}' --filter name=sha256py_web --no-trunc
def047ad1aec5ef91f8c788f5e18a49eeaf5c3b281d778f591751b614d7eeb0f
```

To navigate to that directory:

```console
# cd "/var/lib/docker/containers/$(docker ps --format '{{.ID}}' --filter name=sha256py_web --no-trunc)" && ls
checkpoints
config.v2.json
def047ad1aec5ef91f8c788f5e18a49eeaf5c3b281d778f591751b614d7eeb0f-json.log
hostconfig.json
hostname
hosts
mounts
resolv.conf
resolv.conf.hash
```

Logs on the host are rotated when they reach 200k, with a maximum of 3 files
stored.

## Running tests

If you have the
[`test.py` test runner](https://github.com/paxos-bankchain/devops-test-script/blob/74302a7d911842eb173043b22e0d44951b149a06/test.py),
then you can run it as per the
[`README.md` file](https://github.com/paxos-bankchain/devops-test-script/blob/74302a7d911842eb173043b22e0d44951b149a06/README.md)
from
[`paxos-bankchain/devops-test-script`](https://github.com/paxos-bankchain/devops-test-script),
except that you should [wait for the container to start](./docs/waiting.md) before
using it. Also note that because the container state is persisted on a Docker
volume, you will need to [clean the state](#cleaning-up) before re-running the
test suite.

If you didn't clone this repository with the test script submodule, get it by
running:

```console
$ git submodule update --init
Submodule path 'devops-test-script': checked out '74302a7d911842eb173043b22e0d44951b149a06'
```

### Waiting for the container to start

Either add a sleep function or [wait for the daemon to listen](./docs/waiting.md) when
running unit tests.

```console
$ docker-compose up -d && sleep 2 && ./devops-test-script/test.py -c cert.pem
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

### Cleaning up

The docker container persists data to a volume (so that it works when
restarted). For convenience, a 
[script](./scripts/clean.py)
has been provided to undo the changes
invoked by the test runner. With the container running, do:

```console
$ ./scripts/clean.py --domain localhost --port 5000 --cert-path ./localhost.crt
200
{u'message_deleted': u'2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'}
200
{u'message_deleted': u'fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9'}
```

## Scaling

See [`scaling.md`](./docs/scaling.md)
