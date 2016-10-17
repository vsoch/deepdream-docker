# Google Deepdream + Docker

A Docker Container to run Google's [Deepdream](https://github.com/google/deepdream/). This avoids having to setup all the dependencies (including GPU drivers, Python, Caffe, etc) in your OS of choice, so you can skip right to the fun part!


## Installing

The only dependency you need is [Docker](https://www.docker.com/).


## Building locally

```
docker build -t kennydo/deepdream-docker .
```


## Running

```
docker run \
--rm \
-it \
-p 8888:8888 \
-v /host/path/to/data:/data \
kennydo/deepdream-docker \
jupyter \
notebook \
--port 8888 \
--ip 0.0.0.0 \
--no-browser
```

*Note*: Depending on how much memory your machine has, you might run into problems with high-res images. In my case, processing failed for a 12mp image. Either stick to smaller images or buy more RAM ;-)

