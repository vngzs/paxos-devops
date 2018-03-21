[➥ back to readme](../README.md)

## Scaling

> How would your implementation scale if this were a high throughput service,
> and how could you improve that?

This implementation uses [Sanic](https://github.com/channelcat/sanic), a
Python library that uses the super-fast
[async framework](https://eng.paxos.com/should-i-migrate-to-an-async-framework)
for processing.
This is pretty good for single-container use.

## More than one container

If we want to scale this to more containers on the same host, we can attach the
data volume to more than one docker container and run multiple webservers
behind a load balancer. This will help us if we are limited by:

1. The docker container's processing ability,
2. The docker container's CPU/RAM/network processing,

as long as the host has capacity to handle this. Scaling this way will not help
us if we are limited by I/O on our data volume, because that is a hard limit on
the docker container host.

We can use the [`aiohttp-test.py`](../scripts/aiohttp-test.py) script to
benchmark our application. For example, to generate 500 * 6 random strings of
length 20 and run a POST/GET/DELETE sequence in each of 6 threads, we do:

```
./scripts/aiohttp-test.py -t 6 -c 500 -N 20
avg reqs/sec for thread 4: 328.5040086770064
avg reqs/sec for thread 3: 328.3145973297114
avg reqs/sec for thread 5: 328.03985149520645
avg reqs/sec for thread 2: 326.8089600694861
avg reqs/sec for thread 1: 267.8763297385288
avg reqs/sec for thread 0: 267.0870057271557
total secs: 5.624745474997326. total reqsts: 9000. total reqs/sec: 1600.0724014990703
averaging 307.77179217284913 reqs/second/thread, or 1846 requests in 5.624745474997326 secs
./aiohttp-test.py -t 6 -c 500 -N 20  8.85s user 0.73s system 165% cpu 5.803 total
```

Assuming our benchmarking tool is perfectly optimized (it's not), we can get
~1600 requests per second out of our single-threaded Python webserver, when
serving a "realistic" workload like follows and random 20-character payloads:

```
web_1  | [2018-03-20 03:58:13 +0000] - (sanic.access)[INFO][1:7]: POST https://localhost:5000/messages  201 77
web_1  | [2018-03-20 03:58:13 +0000] - (sanic.access)[INFO][1:7]: GET https://localhost:5000/messages/a85e58f3658f380fa327f44905ee76eaa9db41ab9ae7546bced99a1a4cdd87ec  200 35
web_1  | [2018-03-20 03:58:13 +0000] - (sanic.access)[INFO][1:7]: DELETE https://localhost:5000/messages/a85e58f3658f380fa327f44905ee76eaa9db41ab9ae7546bced99a1a4cdd87ec  200 86
```