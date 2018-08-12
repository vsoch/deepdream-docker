# Google Deepdream + Docker + OpenSource Art

This is a Docker container intended to create [opensource-art](https://vsoch.github.io/opensource-art/)
that is derived from:

 - Google's [Deepdream](https://github.com/google/deepdream/)
 - [saturnism/deepdream-docker](https://github.com/saturnism/deepdream-docker)

The container has been modified to generate a few deep dream images from an input 
image (and other environment variables) with the intended purpose of producing
"Open Source Art," or community contributions of images that have
deepdreams generated in continuous integration. 

## Installing

The only dependency you need is [Docker](https://www.docker.com/).

## Building locally

```
docker build -t vanessa/deepdream .
```

## Running
For a good example of usage, see the [opensource-art](https://www.github.com/vsoch/opensource-art)
repository. We will update here when possible!
