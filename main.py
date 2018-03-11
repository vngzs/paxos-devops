#!/usr/bin/env python3

import logging
import hashlib
import ssl
import os

import json_logging
from sanic import Sanic
from sanic.response import json


app = Sanic()

json_logging.ENABLE_JSON_LOGGING = True
json_logging.init(framework_name='sanic')
json_logging.init_request_instrument(app)

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("/cert.pem", keyfile="/key.pem")

hashmap = {}

@app.route("/messages", methods=["POST"])
async def messages_handler(request):
    m = hashlib.sha256()
    m.update(request.json['message'].encode('utf-8'))
    result = m.hexdigest()
    if not result in hashmap:
        hashmap[result] = request.json['message']
        return json({"digest": result}, status=201)
    else:
        return json({"digest": result}, status=200)

@app.route("/messages/<digest>", methods=["DELETE"])
async def delete(request, digest):
    if not digest in hashmap:
        return json({"err_message": "Message not found"}, status=404)
    else:
        del hashmap[digest]
        return json({"message_deleted": digest})

@app.route("/messages/<digest>", methods=["GET"])
async def test(request, digest):
    if not digest in hashmap:
        return json({"err_message": "Message not found"}, status=404)
    else:
        return json({"message": hashmap[digest]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, ssl=context)
