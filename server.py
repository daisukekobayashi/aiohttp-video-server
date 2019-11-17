import asyncio
import concurrent.futures
import time

import aiohttp
from aiohttp import web
import cv2
import numpy as np
from turbojpeg import TurboJPEG, TJPF_BGR
import uvloop

turbo_jpeg = TurboJPEG()

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

loop = asyncio.get_event_loop()
frame_queue = asyncio.Queue(loop=loop, maxsize=3)
jpeg_queue = asyncio.Queue(loop=loop, maxsize=3)

def encode_jpeg(frame):
    #encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    #return cv2.imencode('.jpg', frame, encode_param)[1].tobytes()
    return turbo_jpeg.encode(frame, 90, TJPF_BGR)

async def async_imshow(title, frame):
    cv2.imshow(title, frame)
    return cv2.waitKey(1) & 0xFF

async def capture(queue):
    video = cv2.VideoCapture(0)
    while True:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            ret, frame = await loop.run_in_executor(pool, video.read)#async_read, video)
        if ret == False:
            continue
        if queue.full():
            await queue.get()
        await queue.put(frame)
        await asyncio.sleep(0.001)

async def jpeg_converter(frame_queue, jpeg_queue):
    while True:
        frame = await frame_queue.get()
        if frame is None:
            break

        with concurrent.futures.ProcessPoolExecutor() as pool:
            jpeg_frame = await loop.run_in_executor(pool, encode_jpeg, frame)
        if jpeg_queue.full():
            await jpeg_queue.get()

        #bgr_array = turbo_jpeg.decode(jpeg_frame)
        #cv2.imwrite('bgr_array_{0}.jpg'.format(time.strftime('%Y%m%d-%H%M%S')), bgr_array)

        await jpeg_queue.put(jpeg_frame)


async def handle_index(request):
    return web.Response(text="Hello, world!")

async def handle_capture(request):
    jpeg_frame = await jpeg_queue.get()
    response = web.Response(
        content_type='image/jpeg',
        body=jpeg_frame
    )
    return response

async def handle_mjpeg_stream(request):
    my_boundary = 'jpegboundary'
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'multipart/x-mixed-replace;boundary={}'.format(my_boundary)
        }
    )

    await response.prepare(request)
    while True:
        frame = await jpeg_queue.get()
        with aiohttp.MultipartWriter('image/jpeg', boundary=my_boundary) as mpwriter:
            mpwriter.append(frame, {
                'Content-Type': 'image/jpeg'
            })
            await mpwriter.write(response, close_boundary=False)
        await response.drain()

if __name__ == '__main__':

    asyncio.ensure_future(capture(frame_queue))
    asyncio.ensure_future(jpeg_converter(frame_queue, jpeg_queue))

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index),
        web.get('/capture', handle_capture),
        web.get('/mjpeg', handle_mjpeg_stream)
    ])

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner)
    loop.run_until_complete(site.start())

    loop.run_forever()

