#!/usr/bin/env python3.6

import argparse
import asyncio
import time
import sys
import string
import json
import random
import multiprocessing as mp

import aiohttp


async def post_message(session, url, message):
    async with session.post(url, json={'message': message}) as resp:
        assert resp.status == 201 or resp.status == 200
        return await resp.text()


async def get_shaurl(session, shaurl):
    async with session.get(shaurl) as resp:
        assert resp.status == 200
        return await resp.text()


async def delete_shaurl(session, shaurl):
    async with session.delete(shaurl) as resp:
        return await resp.text()


async def aio(messages, procnum, avg_dict, count_dict):
    url = 'https://localhost:5000/messages'
    conn = aiohttp.TCPConnector(verify_ssl=False)
    count_dict[procnum] = 0
    async with aiohttp.ClientSession(connector=conn) as session:
        sha = None
        shaurl = None
        start = time.perf_counter()
        for i in range(len(messages)):
            message = messages[i]
            text = await post_message(session, url, message)
            sha = json.loads(text)["digest"]
            shaurl = "{}/{}".format(url, sha)
            count_dict[procnum] += 1
            await get_shaurl(session, shaurl)
            count_dict[procnum] += 1
            await delete_shaurl(session, shaurl)
            count_dict[procnum] += 1
        end = time.perf_counter()
        elapsed = (time.perf_counter() - start)
        avg = count_dict[procnum] / elapsed
        print('avg reqs/sec for thread {}: {}'.format(procnum, avg))
        avg_dict[procnum] = avg

def start_asyncio_processing(messages, procnum, avg_dict, count_dict):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(aio(messages, procnum, avg_dict, count_dict))

def get_n_messages_length_k(n, k):
    return [''.join(random.choices(string.ascii_uppercase + string.digits, k=k))
            for i in range(n)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--threads', type=int, default=1)
    parser.add_argument('-c', '--count', type=int, default=1)
    parser.add_argument('-N', '--length', type=int, default=10)
    args = parser.parse_args()
    manager = mp.Manager()
    avg_dict = manager.dict()
    count_dict = manager.dict()
    jobs = []
    messages_by_thread = [None] * args.threads
    for i in range(args.threads):
        messages_by_thread[i] = get_n_messages_length_k(args.count, args.length)
    start = time.perf_counter()
    for i in range(args.threads):
        p = mp.Process(target=start_asyncio_processing, args=(messages_by_thread[i], i, avg_dict, count_dict))
        jobs.append(p)
        p.start()
    for proc in jobs:
        proc.join()
    end = time.perf_counter()
    elapsed = (end - start)
    reqs = sum(count_dict.values())
    avg = reqs / elapsed
    print('total secs: {}. total reqsts: {}. total reqs/sec: {}'.format(
        elapsed,
        reqs,
        avg,
    ))
    avg_by_thread = sum(avg_dict.values()) / len(avg_dict)
    print("averaging {} reqs/second/thread, or {} requests in {} secs".format(
        avg_by_thread,
        int(avg_by_thread * args.threads),
        elapsed))
    

if __name__ == '__main__':
    main()

