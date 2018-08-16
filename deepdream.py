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

import argparse
import caffe
import shutil
import os
import sys
import random
import tempfile

import warnings
warnings.filterwarnings('ignore', '.*output shape of zoom.*')

# -- Argument Parsing
def get_parser():
    parser = argparse.ArgumentParser(description="DeepDream OpenSource Art")

    parser.add_argument('--input', dest="input", 
                        help="image to run deepdream on, recommended < 1024px", 
                        default=None, type=str)

    parser.add_argument('--layers', dest='layers', action='store_true',
                        help='save images of intermediate layers',
                        default=False)

    parser.add_argument('--guide', dest="guide", 
                        help="second image to guide style of first < 1024px", 
                        default=None, type=str)

    parser.add_argument('--models_dir', dest="models_dir", 
                        help="directory with modules (extracted gist zip) folders", 
                        default='', type=str)

    parser.add_argument('--output_dir', dest="image_output", 
                        help="directory to write dreams", 
                        default='', type=str)

    parser.add_argument('--input_dir', dest="image_dir", 
                        help="directory to write dreams", 
                        default='', type=str)

    parser.add_argument('--layer_filter', dest="filter", 
                        help="if saving --layers, filter based on this string", 
                        default='conv', type=str)

    parser.add_argument('--frames', dest="frames", 
                        help="number of frames to iterate through in dream", 
                        default=5, type=int)

    parser.add_argument('--scale-coeff', dest="s", 
                        help="scale coefficient for each frame", 
                        default=0.25, type=float)

    return parser

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
    
# -- Choose Model

def find_model(models_dir, model_name=None, return_all=False):
    '''find_model will look through a list of folders in some parent models
       directory, and check the folder for the prototext files. If both
       are found for a randomly chosen model, it is returned.

       note:: This model is currently not in use to select, since the models
             would need testing. It is provided so we can implement this :)
    '''
    # Save everything to return to user
    lookup = dict()
    
    models = os.listdir('%s/models' % models_dir)
    print('Found %s candidate models in %s' %(len(models), models_dir))
    
    # 1. Choose a model

    if return_all:
        keepers = []
        for model_name in models:
            model = select_model(model_name)
            if model:
                keepers.append(model)
        return keepers

    while True:

        # If the user provided a model, try it first
        if model_name is None:
            model_name = random.choice(models)

        model = select_model(model_name, models_dir)
        if model:
            return model
        

def select_model(model_name, models_dir):
    '''determine if a model is selectable based on files provided, otherwise
       return none

       Note:: this function currently (in the container) only serves to find
              a specific model that we know to work, as the rest of
              the script isn't generaiized to read it. Given that the models
              are downloaded into the container, this would be a great feature
              so that the model is also randomly selected! See
              https://github.com/vsoch/deepdream-docker/issues/1
    '''

    model_path = os.path.join(models_dir, 'models', model_name)

    # 2. Look (guess) for required files - this should be tested
    # for contributing a model to the repository

    # We need a caffemodel to use it
    params = [x for x in os.listdir(model_path) if x.endswith('caffemodel')]
    if len(params) > 0:            
        lookup = {'model': model_name,
                  'path': model_path,
                  'param_fn': os.path.join(model_path, params[0])}  

        # First effort, look for "deploy" prototext
        deploy_files = [x for x in os.listdir(model_path) if 'deploy' in x]

        # Second effort, look for "deploy" prototext
        if len(deploy_files) > 0:
            lookup['net_fn'] = os.path.join(model_path, deploy_files[0])
            if 'bvlc' in model_path:
                return lookup

    model_name = None


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
              end='inception_4c/output', clip=True, image_output=None,
              save_image=None, **step_params):

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

            # save last image (this could be modified to save sequence or other)
            if save_image is not None and image_output is not None and i==iter_n-1:
                image_file = "%s/%s_%s-%s" % (image_output, end, i, save_image)

                # The keys have directory / in them, may need to mkdir
                image_dir = os.path.dirname(image_file)
                if not os.path.exists(image_dir):
                    # not entirely safe way to do it, but ok for now
                    os.makedirs(image_dir)

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

def objective_guide(dst):
    x = dst.data[0].copy()
    y = dst.data[0].copy()
    ch = x.shape[0]
    x = x.reshape(ch,-1)
    y = y.reshape(ch,-1)
    A = x.T.dot(y) # compute the matrix of dot-products with guide features
    dst.diff[0].reshape(ch,-1)[:] = y[:,A.argmax(1)] # select ones that match best


def visualize_layers(net, img, image_output, input_name, layer_filter="conv"):
    for end,blob in net.blobs.items():
        if layer_filter in end:
            try:
                out = deepdream(net, img, end=end)
                outname = "%s/layer-%s-%s" % (image_output, end.replace('/','-'), input_name)
                PIL.Image.fromarray(np.uint8(out)).save(outname)
            except: # not in list
                print('Issue with %s, skipping' % end)
                pass


def main():

    parser = get_parser()

    def help(return_code=0):
        parser.print_help()
        sys.exit(return_code)
    
    # If the user didn't provide any arguments, show the full help
    try:
        args = parser.parse_args()
    except:
        sys.exit(0)

    tmpdir = tempfile.mkdtemp()
    models_dir = get_envar('DEEPDREAM_MODELS', args.models_dir)
    frames = int(os.environ.get('DEEPDREAM_FRAMES', args.frames))
    s = float(os.environ.get('DEEPDREAM_SCALE_COEFF', args.s)) # scale coefficient
    image_dir = os.environ.get('DEEPDREAM_IMAGES', args.image_dir)
    image_output = args.image_output or os.environ.get('DEEPDREAM_OUTPUT', tmpdir)
    image_input =  os.environ.get('DEEPDREAM_INPUT', args.input) or '/deepdream/deepdream/sky1024px.jpg'


    # -- Input Checking
                        
    if not os.path.exists(image_output):
        os.makedirs(image_output)

    if not os.path.exists(image_input):

        # Second try - user mounted to data, but image is in $PWD
        image_input = "/data/%s" % image_input

        if not os.path.exists(image_input):
            print('Cannot find %s.' % image_input)
            sys.exit(1)


    # Choose random model
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

    # --- Dream!

    input_name = os.path.basename(image_input)
    img = np.float32(PIL.Image.open(image_input))
    dreamy = deepdream(net, img)

    PIL.Image.fromarray(np.uint8(dreamy)).save("%s/dreamy-%s" % (image_output, input_name))

    # --- Save Layers

    # net.blobs.keys() we can change layer selection to alter the result! 

    if args.layers is True:
        print('Saving subset of layers to %s' % image_output)
        visualize_layers(net, img, image_output, input_name, args.filter)

    # --- With Guide?
    if args.guide is not None:
        guide = np.float32(PIL.Image.open(args.guide))
        end = 'inception_3b/output'
        h, w = guide.shape[:2]
        src, dst = net.blobs['data'], net.blobs[end]
        src.reshape(1,3,h,w)
        src.data[0] = preprocess(net, guide)
        net.forward(end=end)
        guide_features = dst.data[0].copy()
        guided = deepdream(net, img, end=end, objective=objective_guide)
        PIL.Image.fromarray(np.uint8(guided)).save("%s/guided-%s" % (image_output, input_name))
        img = guided

    frame = img
    frame_i = 0

    h, w = frame.shape[:2]
    for i in xrange(frames):
        frame = deepdream(net, frame)
        PIL.Image.fromarray(np.uint8(frame)).save("%s/frame-%04d-%s" % (image_output, frame_i, input_name))
        frame = nd.affine_transform(frame, [1-s,1-s,1], [h*s/2,w*s/2,0], order=1)
        frame_i += 1

    print('DeepDreams are made of cheese, who am I to diss a brie?')
    print('output> %s' % image_output)

    # Remove temporary parameters, we could keep this if someone wanted
    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    main()
