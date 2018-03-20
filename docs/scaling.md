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

