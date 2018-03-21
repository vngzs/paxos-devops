#!/usr/bin/env python3

import asyncio
import hashlib
import ssl
import sys
import os
import signal
from pathlib import Path
import logging
from json import dumps
from concurrent.futures import ProcessPoolExecutor

from sanic import Sanic
from sanic.response import json
from sanic.response import file

import aiofiles
from aiofiles import os as async_os

app = Sanic('sha256py')

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
if len(sys.argv) > 1:
    context.load_cert_chain(sys.argv[1], keyfile=sys.argv[2])
else:
    context.load_cert_chain("/cert.pem", keyfile="/key.pem")

logger = logging.getLogger('root')
error_logger = logging.getLogger('sanic.error')
access_logger = logging.getLogger('sanic.access')

def sha256_encode(message):
    b = message
    if not type(b) == bytes:
        b = message.encode('utf-8')
    m = hashlib.sha256()
    m.update(b)
    return m.hexdigest()


def mkdir_to_path(directory, path):
    directory.mkdir(exist_ok=True)
    logger.info("creating path: %s", str(path))
    path.touch()


def unlink(path):
    logger.info("creating path: %s", str(path))
    path.touch()


class DirHashMap(object):
    def __init__(self, loop=None, root='/srv'):
        self.loop = loop
        self.root = Path(root)

    async def add(self, item):
        """Insert item into the DirHashMap

        Args:
            item: will be sha256 encoded and stored on the filesystem at
                  root / sha256(item)[:2] / sha256(item).
        """
        result = await self.loop.run_in_executor(None, sha256_encode, item)
        logger.info('adding %s -> %s', str(result), str(item))
        contains = await self.contains(result)
        if not contains:
            directory = self.root / Path(result[:2])
            path = directory / Path(result)
            await self.loop.run_in_executor(None, mkdir_to_path, directory, path)
            async with aiofiles.open(path, mode='w') as f:
                await f.write(dumps({"message": item}))
            return {"digest": result, "updated": True}
        else:
            return {"digest": result, "updated": False}

    async def getitem(self, key):
        if len(key) != 64:
            raise KeyError(key)
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        return await file(path)

    async def contains(self, key):
        if len(key) != 64:
            return False
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        return await self.loop.run_in_executor(None, path.is_file)

    async def delitem(self, key):
        if len(key) != 64:
            raise KeyError(key)
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        if not path.exists():
            raise KeyError(key)
        if not path.is_file():
            raise KeyError(key)
        return await self.loop.run_in_executor(None, path.unlink)


hashmap = None


@app.listener('before_server_start')
def init(sanic, loop):
    global hashmap
    hashmap = DirHashMap(loop=loop)


@app.route("/messages", methods=["POST"])
async def send_message(request):
    logger.info('sending message: %s', str(request.json['message']))
    result = await hashmap.add(request.json['message'])
    logger.info('%s %s %s', str(request.json['message']), ' -> ', str(result['digest']))
    if result['updated']:
        logger.info('returning 201: %s', str(result['digest']))
        return json({"digest": result['digest']}, status=201)
    else:
        logger.info('returning 200: %s', str(result['digest']))
        return json({"digest": result['digest']}, status=200)


@app.route("/messages/<digest>", methods=["DELETE"])
async def delete(request, digest):
    """Delete a message at digest.

    Convenience function for when this is run with persistent docker volumes,
    such that test messages may be automatically deleted.
    """
    contains = await hashmap.contains(digest)
    if not contains:
        return json({"err_message": "Message not found"}, status=404)
    else:
        await hashmap.delitem(digest)
        return json({"message_deleted": digest})


@app.route("/messages/<digest>", methods=["GET"])
async def retrieve_message(request, digest):
    contains = await hashmap.contains(digest)
    if not contains:
        error_logger.error('digest %s not found', str(digest))
        return json({"err_message": "Message not found"}, status=404)
    else:
        return await hashmap.getitem(digest)


def main():
    app.run(host="0.0.0.0", port=5000, ssl=context, workers=20)

if __name__ == "__main__":
    main()
