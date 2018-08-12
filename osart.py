#!/usr/bin/env python

# DeepDream OpenSource-Art
# Much of the source code here is derived from 
#      https://github.com/saturnism/deepdream-docker
# which in turn is derived from 
#     https://github.com/google/deepdream
# and modified to integrate into the OpenSource Art Project

from cStringIO import StringIO
import numpy as np
import scipy.ndimage as nd
import PIL.Image
from IPython.display import clear_output, Image, display
from google.protobuf import text_format

import caffe
import os
import random
import tempfile


# -- Environment Variables

def get_envar(name, default=None):
    '''get an environment variable with "name" and
       check that it exists as a file or folder on the filesystem.
       If not defined, or doesn't exist, exit on error.
    '''
    value = os.environ.get(name, default)

    if not value:
        print('Please export %s' % value)
        sys.exit(1)

    if not os.path.exists(value):
        print('%s does not exist! Is it inside the container?' % value)
        sys.exit(1)

    return value

# Write temporary prototxt
tmpdir = tempfile.mkdtemp()

frame_dir = '%s/frames' % tmpdir
if not os.path.exists(frame_dir):
    os.mkdir(frame_dir)

models_dir = get_envar('DEEPDREAM_MODELS')
image_dir = os.environ.get('DEEPDREAM_IMAGES')
image_output = os.environ.get('DEEPDREAM_OUTPUT', tmpdir)
image_input = os.environ.get('DEEPDREAM_INPUT', 
                             '/deepdream/deepdream/sky1024px.jpg')

# -- Choose Model

def find_model(models_dir, model_name=None):
    '''find_model will look through a list of folders in some parent models
       directory, and check the folder for the prototext files. If both
       are found for a randomly chosen model, it is returned.

       note:: This model is currently not in use to select, since the models
             would need testing. It is provided so we can implement this :)
    '''
    # Save everything to return to user
    lookup = dict()
    
    models = os.listdir(models_dir)
    print('Found %s candidate models in %s' %(len(models), models_dir))
    
    # 1. Choose a model
    while True:

        # If the user provided a model, try it first
        if model_name is None:
            model_name = random.choice(models)

        model_path = os.path.join(models_dir, model_name)

        # 2. Look (guess) for required files - this should be tested
        # for contributing a model to the repository

        deploy_files = [x for x in os.listdir(model_path) if 'deploy' in x]
        if len(deploy_files) > 0:
            lookup = {'model': model_name,
                      'path': model_path,
                      'param_fn': None,
                      'net_fn': os.path.join(model_path, deploy_files[0])}  

            # Is there already a cached parameters?
            params = [x for x in os.listdir(model_path) if x.endswith('caffemodel')]
            if len(params) > 0:
                lookup['param_fn'] = os.path.join(model_path, params[0])
            return lookup

lookup = find_model(models_dir, 'bvlc_googlenet')


# -- Loading DNN Model

# Patching model to be able to compute gradients.
# Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
model = caffe.io.caffe_pb2.NetParameter()
text_format.Merge(open(lookup['net_fn']).read(), model)
model.force_backward = True

tmp_proto = '%s/tmp.prototxt' % tmpdir
open(tmp_proto, 'w').write(str(model))

net = caffe.Classifier(tmp_proto, lookup['param_fn'],
                       mean = np.float32([104.0, 116.0, 122.0]), # ImageNet mean, training set dependent
                       channel_swap = (2,1,0)) # the reference model has channels in BGR order instead of RGB

# a couple of utility functions for converting to and from Caffe's input image layout
def preprocess(net, img):
    return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']
def deprocess(net, img):
    return np.dstack((img + net.transformer.mean['data'])[::-1])

# If your GPU supports CUDA and Caffe was built with CUDA support,
# uncomment the following to run Caffe operations on the GPU.
# caffe.set_mode_gpu()
# caffe.set_device(0) # select GPU device if multiple devices exist

def showarray(a, fmt='jpeg'):
    a = np.uint8(np.clip(a, 0, 255))
    f = StringIO()
    PIL.Image.fromarray(a).save(f, fmt)
    display(Image(data=f.getvalue()))


# -- DeepDream Functions

def objective_L2(dst):
    dst.diff[:] = dst.data 

def make_step(net,
              step_size=1.5,
              end='inception_4c/output', 
              jitter=32,
              clip=True,
              objective=objective_L2):

    '''Basic gradient ascent step.'''

    # input image is stored in Net's 'data' blob
    src = net.blobs['data']
    dst = net.blobs[end]

    ox, oy = np.random.randint(-jitter, jitter+1, 2)
    src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2) # apply jitter shift
            
    net.forward(end=end)
    objective(dst)  # specify the optimization objective
    net.backward(start=end)
    g = src.diff[0]

    # apply normalized ascent step to the input image
    src.data[:] += step_size/np.abs(g).mean() * g
    src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2) # unshift image
            
    if clip:
        bias = net.transformer.mean['data']
        src.data[:] = np.clip(src.data, -bias, 255-bias)  

def deepdream(net, base_img, iter_n=10, octave_n=4, octave_scale=1.4, 
              end='inception_4c/output', clip=True, frame_dir=None,
              save_image=False, **step_params):

    # prepare base images for all octaves
    octaves = [preprocess(net, base_img)]

    for i in xrange(octave_n-1):
        octaves.append(nd.zoom(octaves[-1], (1, 1.0/octave_scale,1.0/octave_scale), order=1))
    
    src = net.blobs['data']
    detail = np.zeros_like(octaves[-1]) # allocate image for network-produced details
    for octave, octave_base in enumerate(octaves[::-1]):

        h, w = octave_base.shape[-2:]
        if octave > 0:
            # upscale details from the previous octave
            h1, w1 = detail.shape[-2:]
            detail = nd.zoom(detail, (1, 1.0*h/h1,1.0*w/w1), order=1)

        src.reshape(1,3,h,w) # resize the network's input image size
        src.data[0] = octave_base+detail

        for i in xrange(iter_n):
            make_step(net, end=end, clip=clip, **step_params)
            
            # visualization
            vis = deprocess(net, src.data[0])

            # save last image?
            if save_image is True and frame_dir is not None and i==iter_n-1:
                image_file = "%s/%s_%s.jpg" % (frame_dir, end, i)

                # The keys have directory / in them, may need to mkdir
                image_dir = os.path.dirname(image_file)
                if not os.path.exists(image_dir):
                    os.mkdir(image_dir)

                PIL.Image.fromarray(np.uint8(vis)).save(image_file)

            if not clip: # adjust image contrast if clipping is disabled
                vis = vis*(255.0/np.percentile(vis, 99.98))
            showarray(vis)
            print(octave, i, end, vis.shape)
            clear_output(wait=True)
            
        # extract details produced on the current octave
        detail = src.data[0]-octave_base

    # returning the resulting image
    return deprocess(net, src.data[0])

# --- Dream!

img = np.float32(PIL.Image.open(image_input))
deepdream(net, img, 
          save_image=True,
          frame_dir=frame_dir)

PIL.Image.fromarray(np.uint8(img)).save("%s/original.jpg" % frame_dir)

# TODO: net.blobs.keys() we can change layer selection to alter the result! 

frame = img
frame_i = 0

h, w = frame.shape[:2]
s = 0.2 # scale coefficient
for i in xrange(3):
    frame = deepdream(net, frame)
    PIL.Image.fromarray(np.uint8(frame)).save("%s/inception_4c/frame-%04d.jpg"% (frame_dir, frame_i))
    frame = nd.affine_transform(frame, [1-s,1-s,1], [h*s/2,w*s/2,0], order=1)
    frame_i += 1

print('DeepDreams are made of cheese, who am I to diss a brie?')
print('output> %s' % image_output)
