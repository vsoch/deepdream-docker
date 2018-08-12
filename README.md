# Google Deepdream + Docker

A Docker Container to run Google's [Deepdream](https://github.com/google/deepdream/), modified from
the fantastic [kennydo](https://github.com/kennydo/deepdream-docker)!  The container
has been modified to serve functions to choose N images from a folder, and then
to take in some N images to run through the algorithm (and generate a new image). Specifically
we want to:

 1. Have a command to randomly select images
 2. Do preprocessing of those images to conform to some size
 3. Generate a new image with the N images

## Installing

The only dependency you need is [Docker](https://www.docker.com/).

## Building locally

```
docker build -t vanessa/deepdream .
```

## Running

```
docker run \
--rm \
-it \
-p 8888:8888 \
-v /host/path/to/data:/data \
vanessa/deepdream-docker \
sudo \
jupyter \
notebook \
--port 8888 \
--ip 0.0.0.0 \
--no-browser
```

*Note*: Depending on how much memory your machine has, you might run into problems with high-res images. In my case, processing failed for a 12mp image. Either stick to smaller images or buy more RAM ;-)

