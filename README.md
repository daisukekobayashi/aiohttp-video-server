# aiohttp-video-server

This is video server implementation using aiohttp. Capturing image using OpenCV and streaming it via HTTP.

## Usage

```sh
$ python server.py -h
usage: server.py [-h] [--host HOST] [--port PORT]

aiohttp video server

optional arguments:
  -h, --help   show this help message and exit
  --host HOST
  --port PORT
```

After running server.py script, you can see streaming on ``http://localhost:8080/mjpeg`` and you can capture a single image on ``http://localhost:8080/capture``
