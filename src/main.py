#!/usr/bin/env python3

import hashlib
import ssl
import sys
import os
import signal
from pathlib import Path
from json import dumps

from sanic import Sanic
from sanic.response import json
from sanic.response import file

import aiofiles

app = Sanic('sha256py')

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("/cert.pem", keyfile="/key.pem")


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
        m = hashlib.sha256()
        b = item
        if not type(b) == bytes:
            b = item.encode('utf-8')
        m.update(b)
        result = m.hexdigest()
        print('adding {} -> {}'.format(result, item))
        if not result in self:
            directory = self.root / Path(result[:2])
            directory.mkdir(exist_ok=True)
            path = directory / Path(result)
            path.touch()
            async with aiofiles.open(path, mode='w') as f:
                await f.write(dumps({"message": item}))
            return {"digest": result, "updated": True}
        else:
            return {"digest": result, "updated": False}

    async def __getitem__(self, key):
        if len(key) != 64:
            raise KeyError(key)
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        return await file(path)

    def __contains__(self, key):
        if len(key) != 64:
            return False
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        return path.is_file()

    def __delitem__(self, key):
        if len(key) != 64:
            raise KeyError(key)
        path = self.root / Path(key[:2]) / Path(key)
        if not self.root in path.parents:
            raise ArgumentError('bad path')
        if not path.exists():
            raise KeyError(key)
        if not path.is_file():
            raise KeyError(key)
        path.unlink()


hashmap = None


@app.listener('before_server_start')
def init(sanic, loop):
    global hashmap
    hashmap = DirHashMap(loop=loop)


@app.route("/messages", methods=["POST"])
async def send_message(request):
    print('sending message: {}'.format(request.json['message']))
    result = await hashmap.add(request.json['message'])
    print(request.json['message'], ' -> ', result['digest'])
    if result['updated']:
        print('returning 201', result['digest'])
        return json({"digest": result['digest']}, status=201)
    else:
        print('returning 200', result['digest'])
        return json({"digest": result['digest']}, status=200)


@app.route("/messages/<digest>", methods=["DELETE"])
async def delete(request, digest):
    """Delete a message at digest.

    Convenience function for when this is run with persistent docker volumes,
    such that test messages may be automatically deleted.
    """
    if not digest in hashmap:
        return json({"err_message": "Message not found"}, status=404)
    else:
        del hashmap[digest]
        return json({"message_deleted": digest})


@app.route("/messages/<digest>", methods=["GET"])
async def retrieve_message(request, digest):
    if not digest in hashmap:
        print('digest {} not found'.format(digest))
        return json({"err_message": "Message not found"}, status=404)
    else:
        return await hashmap[digest]


def main():
    app.run(host="0.0.0.0", port=5000, ssl=context, workers=20)

if __name__ == "__main__":
    main()
