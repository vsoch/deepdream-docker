#!/bin/bash

# Download models from the Caffe Model-Zoo
# https://github.com/BVLC/caffe/wiki/Model-Zoo
# See associated licenses for each on wiki page

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# intended for structure in container vanessa/deepdream
DEST="${1:-/deepdream/caffe/models}"

echo "Script Directory: ${HERE}";
echo "Models Directory: ${DEST}":

# Format is download_model_from_gist.sh <gist_id> <models_dir>
for zoo in $(cat ${HERE}/zoo.txt)
    do
    /bin/bash ${HERE}/download_model_from_gist.sh ${zoo} ${DEST}
    folder_name=$(echo ${zoo//\//-})
    if [ -f "$DEST/$folder_name/readme.md" ]
        then
            echo "Downloading ${zoo}"
            python $HERE/download_model_binary.py ${DEST}/${folder_name};
    fi
done
