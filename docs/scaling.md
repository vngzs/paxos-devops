[➥ back to readme](../README.md)

## Scaling

> How would your implementation scale if this were a high throughput service,
> and how could you improve that?

This implementation uses [Sanic](https://github.com/channelcat/sanic), a
Python library that uses the super-fast
[async framework](https://eng.paxos.com/should-i-migrate-to-an-async-framework)
for processing.
This is pretty good for single-container use.

### Benchmarking

We can use the [`aiohttp-test.py`](../scripts/aiohttp-test.py) or its wrapper,
[`run-aiohttp-test.sh`](../scripts/run-aiohttp-test.sh) script to
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

This still is not terrible - a recent
[scaling blog post](https://getstream.io/blog/stream-and-go-news-feeds-for-over-300-million-end-users/)
wrote about building an API in Go that services ~20k requests per minute,
albeit with a much more complex service. Based on my benchmarks, we should be
able to handle ~90k requests per minute on my laptop, which is not bad for
a short Python script.

#### Limitations

Basically, we are limited by the throughput and performance of our single
Docker container and single Python application. As soon as this becomes slow,
it is time to start re-architecturing our application.

### More than one container?

If we want to scale this to more containers on the same host, we can attach the
data volume to more than one docker container and run multiple webservers
behind a load balancer. This will help us if we are limited by:

1. The docker container's processing ability,
2. The docker container's CPU/RAM/network processing,

as long as the host has capacity to handle this. Scaling this way will not help
us if we are limited by I/O on our data volume, because that is a hard limit on
the docker container host.

But _ultimately this is kind of a bad idea_, since we risk concurrency issues
if two containers try to write to the same file.

### Load balancing

If we want more than one application container, we need to load balance the
applications somehow. A neat example of this would be
[haproxy](https://github.com/docker/dockercloud-haproxy/tree/master)
in front of our Docker application servers, but any load balancer that is
production-grade and can send traffic to our containers would do.

### Offloading persistent storage

If we offload our persistent storage to something besides Docker data volumes,
then we can scale our application servers separately from our data store. This
solves the concurrency issue mentioned in
[More than one container?](#more-than-one-container).

In this case, assume we choose [Cassandra](http://cassandra.apache.org/) for
our persistent storage. We change our applications to write and read to our
Cassandra cluster instead of a Docker volume. Since Cassandra
[writes are atomic at the row-level](https://docs.datastax.com/en/cassandra/3.0/cassandra/dml/dmlTransactionsDiffer.html),
this automatically solves the concurrency problems related to sharing a docker
volume across hosts.

For example, in this case we could store the primary key as `text` data type,
which would be the sha256 checksum of our message. The message could also fit
nicely into a `text` data type, given our current use case. If we need to store
messages longer than the 64 KB limit, we could use the `blob` data type for
messages.

With the sha256 checksum as our primary key, we should achieve reasonable
[consistent hashing](https://docs.datastax.com/en/cassandra/2.1/cassandra/architecture/architectureDataDistributeHashing_c.html).
This gives us high availability (by running multiple application servers
behind a load balancer) and scalability in our persistent storage (we can add
more Cassandra nodes to handle a higher workload).

#### Other options

We could use another database for persistent storage, but I picked Cassandra
because of its scalability, row-level atomic updates, and ease of use.

Using Amazon S3 for persistence is another option. While S3 is eventually
consistent in general, it provides read-after-write consistency. Since it is
extremely unlikely we will ever encounter a sha256 collision over the course of
our application's lifetime, and DELETE requests are not in the original spec
(though I implemented them for testing purposes), this is good enough for our
use case.

However, if we end up with a GET-heavy workload, Amazon might
[rate limit our application](https://docs.aws.amazon.com/AmazonS3/latest/dev/request-rate-perf-considerations.html).
In this case, again given that we do not support updates or deletes, we could
run
[CloudFront over S3](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/MigrateS3ToCloudFront.html)
to manage a GET-heavy workload. We could remake this service using S3 for
persistent storage relatively quickly - it would probably not be much more
code implemented using S3.

The other benefit of S3 would be its streaming capabilities. Rather than
reading entire files into our application servers before returning them to our
clients, we could stream (large) files back piece-by-piece.

#### Performance bounds

Since we are offloading our I/O to Cassandra and mostly serving and storing
messages from a ReST API, chances are our system will be I/O bound. However,
if we find the sha256 calculation is meaningfully limiting (this will be
obvious because we will either be storing large messages or the CPU usage on
our Python application servers will be high), we can always rewrite our app
servers in a language like [Go](https://golang.org/) to make this more
efficient.

The same holds true for an S3-based implementation. An added benefit there
would be, again, the streaming capability: we can lower RAM usage in our app
servers by avoiding keeping entire response objects in memory.
