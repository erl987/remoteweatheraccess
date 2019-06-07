import time
from datetime import datetime, timedelta
import numpy as np

from aiohttp import ClientSession, TCPConnector
import asyncio

URL = "http://server-sol:5000/api/v1/data"
NUM_REQUESTS = 500
PARALLEL_REQUESTS_LIMIT = 70

FIRST_TIME = datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0)
DELTA_TIME = timedelta(minutes=1)

_num_failed = 0
_num_non_200 = 0


async def fetch(url, session, curr_time):
    global _num_failed
    global _num_non_200

    try:
        data = {"timepoint": curr_time.isoformat(),
                "temp": np.random.uniform(-25.0, 45.0),
                "humidity": np.random.uniform(0.0, 100.0)}

        async with session.post(url, json=data) as response:
            await response.read()
            status = response.status
            print("Response status: {}".format(status))
            print("Response body: {}".format(await response.json()))

            if status < 200 or status >= 300:
                _num_non_200 += 1
            return
    except Exception as e:
        print(e)
        _num_failed += 1


async def bound_fetch(semaphore, url, session, curr_time):
    async with semaphore:
        await fetch(url, session, curr_time)


async def run(session, num_requests):
    tasks = []
    curr_time = FIRST_TIME

    semaphore = asyncio.Semaphore(PARALLEL_REQUESTS_LIMIT)
    for i in range(num_requests):
        task = asyncio.ensure_future(bound_fetch(semaphore, URL, session, curr_time))
        tasks.append(task)
        curr_time += DELTA_TIME

    responses = asyncio.gather(*tasks)
    await responses


async def main():
    connector = TCPConnector(limit=None)
    async with ClientSession(connector=connector) as session:
        await run(session, NUM_REQUESTS)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    start_time = time.time()
    loop.run_until_complete(main())
    end_time = time.time()

    elapsed_time = end_time - start_time
    requests_per_sec = NUM_REQUESTS / elapsed_time

    print("{} requests took {:.1f} s, this is {:.0f} requests/s, {} failures, {} non-200 status codes".
          format(NUM_REQUESTS, elapsed_time, requests_per_sec, _num_failed, _num_non_200))
