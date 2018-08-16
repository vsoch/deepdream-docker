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

## Usage

> How do I build the container?

```
docker build -t vanessa/deepdream .
```

Optionally, you can add a version:

```
docker build -t vanessa/deepdream:0.0.8 .
```

> How do I run the container?

Generally, you should have some folder with images (inputs and outputs) that you will bind to the container,
and then run it. We have provided an example [data](data) folder to get you started. Notice that it has two
subfolders, `inputs` and `outputs` that are expected by the container. The input image provided
as a variable is also relative to _inside the container_. You can either specify input arguments (see below)
or environment variables for inputs.


### Command Line

```bash
docker run vanessa/deepdream:0.0.9 --help
...
usage: deepdream.py [-h] [--input INPUT] [--guide GUIDE]
                    [--models_dir MODELS_DIR] [--output_dir IMAGE_OUTPUT]
                    [--input_dir IMAGE_DIR] [--frames FRAMES]
                    [--scale-coeff S]

DeepDream OpenSource Art

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         image to run deepdream on, recommended < 1024px
  --guide GUIDE         second image to guide style of first < 1024px
  --models_dir MODELS_DIR
                        directory with modules (extracted gist zip) folders
  --output_dir IMAGE_OUTPUT
                        directory to write dreams
  --input_dir IMAGE_DIR
                        directory to write dreams
  --frames FRAMES       number of frames to iterate through in dream
  --scale-coeff S       scale coefficient for each frame
```

For example:

```bash
docker run -v $PWD/data:/data vanessa/deepdream --input /data/inputs/tim-holman-circle-packing.jpg
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

> Can I combine two images?

Yes! You can provide a second image as a "guide"

```bash
docker run -v $PWD/data:/data vanessa/deepdream --input /data/inputs/tim-holman-circle-packing.jpg --guide /data/inputs/natacha-sochat-goldie.jpg
```

In all cases, it's recommended to start with smaller images, see the result, and work your way up.

> How do I save the layers?

You can add the flag `--layers` to run the algorithm using every layer as a guide. Note that
for large images this might take a really long time, and it's recommended to do with smaller
images first!

```bash
docker run -v $PWD/data:/data vanessa/deepdream --input /data/inputs/tim-holman-circle-packing.jpg --layers
```


### Environment Variables
See the [deepdreams.py](deepdreams.py) and [run.sh](run.sh) and [Dockerfile](Dockerfile)
for arguments you can set, if this is your preference.

> What parameters can I change?

The parameters are controlled via environment variables that start with `DEEPDREAM_*`
Some are provided by default from the container, others are set in run.sh (also in the container,
and changeable if you set them at runtime). See the [run.sh](run.sh) file for a summary.

## More Examples
So, for example, to run over an entire directory of input images, just do this:

```bash
for image in $(ls data/inputs/circle*)
    do
    echo "Processing $image"
    docker run -v $PWD/data:/data vanessa/deepdream --input /$image
done
```

For a good example of usage, see the [opensource-art](https://www.github.com/vsoch/opensource-art)
repository. We will update here when possible!

### Development

If you want to shell into the container to play around (or get it started running and interact with
it otherwise) it's easy to run, change the entrypoint to be bash, and give it a good name:

```bash
# nature.jpg is in the present working directory
$ docker run --name osart -v $PWD:/data -it --entrypoint bash vanessa/deepdream:0.0.9
root@4dd0ba3a02a5:/deepdream#
```

Then from the outside, for example, you can test an image in the $PWD like so:

```bash
docker exec osart python /dims.py --image /data/nature.jpg
docker exec osart python /dims.py --image /data/nature.jpg --width
```
