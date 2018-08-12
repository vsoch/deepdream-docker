#!/bin/bash

# Run OpenSource Art!

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# DEEPDREAM_INPUT is the first argument
# If not defined, set as '/deepdream/deepdream/sky1024px.jpg'
# DEEPDREAM_MODELS is defined with container /deepdream/caffe/models
# Data is mapped at /data, including subfolders for input and output

export DEEPDREAM_IMAGES=/data/inputs
export DEEPDREAM_OUTPUT=/data/outputs
export DEEPDREAM_INPUT="${1}"

echo "Images Directory: ${DEEPDREAM_IMAGES}";
echo "Output Directory: ${DEEPDREAM_OUTPUT}":

python ${HERE}/deepdream.py
