#!/bin/bash

source config.sh

mkdir -p $DIR/data
BOOL=${1}
REALS=${2}
DEPTH=${3}
SEED=666

python3 generate.py -b "$BOOL" -r "$REALS" -d "$DEPTH" -s $SEED -o $DIR/data -m 100