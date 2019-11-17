import asyncio
import concurrent.futures

import aiohttp
import cv2
import numpy as np
from turbojpeg import TurboJPEG, TJPF_BGR
import uvloop

turbo_jpeg = TurboJPEG()

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()

def decode_jpeg(frame):
    return turbo_jpeg.decode(frame)

async def capture(client):
    async with client.get('http://localhost:8080/capture') as resp:
        assert resp.status == 200
        return await resp.read()

async def main():
    async with aiohttp.ClientSession() as client:
        while True:
            jpeg = await capture(client)
            with concurrent.futures.ProcessPoolExecutor() as pool:
                bgr_array = await loop.run_in_executor(pool, decode_jpeg, jpeg)
            cv2.imshow('live view', bgr_array)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == '__main__':
    loop.run_until_complete(main())
