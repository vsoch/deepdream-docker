# Google Deepdream + Docker + OpenSource Art

![data/example/frame-0002.jpg](data/example/frame-0002.jpg)

This is a Docker container intended to create [opensource-art](https://vsoch.github.io/opensource-art/)
that is derived from:

 - Google's [Deepdream](https://github.com/google/deepdream/)
 - [saturnism/deepdream-docker](https://github.com/saturnism/deepdream-docker)

The container has been modified to generate a few deep dream images from an input 
image (and other environment variables) with the intended purpose of producing
"Open Source Art," or community contributions of images that have
deepdreams generated in [continuous integration](https://github.com/vsoch/opensource-art/blob/master/.circleci/config.yml).  
See more [examples](data/examples) in the examples folder. 

## Installing

The only dependency you need is [Docker](https://www.docker.com/).

## Building locally

```
docker build -t vanessa/deepdream .
```

## Usage

Generally, you should have some folder with images (inputs and outputs) that you will bind to the container,
and then run it. We have provided an example [data](data) folder to get you started. Notice that it has two
subfolders, `inputs` and `outputs` that are expected by the container. The input image provided
as a variable is also relative to _inside the container_.

```bash
docker run -v $PWD/data:/data vanessa/deepdream /data/inputs/tim-holman-circle-packing.jpg
...
<IPython.core.display.Image object>
(3, 9, 'inception_4c/output', (320, 320, 3))
DeepDreams are made of cheese, who am I to diss a brie?
output> /data/outputs
```

As indicated above, the output images are now in `data/outputs`:

```bash
$ tree data/outputs/
data/outputs/
├── inception_4c
│   ├── frame-0000.jpg
│   ├── frame-0001.jpg
│   └── output_9.jpg
└── original.jpg  
```

## More Examples
So, for example, to run over an entire directory of input images, just do this:

```bash
for image in $(ls data/inputs/circle*)
    do
    echo "Processing $image"
    docker run -v $PWD/data:/data vanessa/deepdream /$image
done
```

For a good example of usage, see the [opensource-art](https://www.github.com/vsoch/opensource-art)
repository. We will update here when possible!
