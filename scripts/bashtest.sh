#!/bin/bash

docker exec -i -t "$(docker ps | sed -n 2p | awk '{ print $1 }')" /bin/bash
