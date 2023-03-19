#!/bin/bash

source config.sh

DATA_FILE=files.txt
DATA_DIR=data

# check if data DIR/data exists
if [ ! -d ${DATA_DIR}/ ]; then
  wget --directory-prefix=$DATA_DIR --input-file=$DATA_FILE
fi

mkdir -p $DIR/data
for file in $(ls $DATA_DIR); do
  python3 generate.py $DATA_DIR/$file -o $DIR/data -m 5
done