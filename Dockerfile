FROM saturnism/deepdream

# docker build -t vanessa/deepdream .
# docker run -it vanessa/deepdream bash

LABEL MAINTAINER vsochat@stanford.edu

# Unzip and wget dependencies
RUN apt-get update && apt-get install -y wget unzip

ADD . /deepdream/caffe/scripts
ADD ./deepdream.py /deepdream.py
ADD ./run.sh /run.sh
WORKDIR /deepdream/caffe/models

# Environment variables for deepdream
ENV DEEPDREAM_OUTPUT /data/outputs
ENV DEEPDREAM_MODELS /deepdream/caffe
ENV CAFFE_SCRIPTS /deepdream/caffe/scripts

# Download extra models
# wget https://raw.githubusercontent.com/wiki/BVLC/caffe/Model-Zoo.md -O zoo.md
# cat zoo.md | grep -o -P '(?<=gist[.]github[.]com).*(?=[)])' # (gets most)
RUN cd /deepdream/caffe/models && \
    echo "Downloading extra models..." && \
    chmod u+x ${CAFFE_SCRIPTS}/download_zoo.sh && \
    /bin/bash ${CAFFE_SCRIPTS}/download_zoo.sh ${PWD}

# disable opencv camera driver
RUN ln /dev/null /dev/raw1394

# Additional updates to pip
RUN pip install --upgrade pip && \
    pip install ptpython && \
    mkdir -p data/outputs data/inputs

WORKDIR /deepdream
ENTRYPOINT ["/bin/bash", "/run.sh"]
