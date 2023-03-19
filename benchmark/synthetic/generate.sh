#!/bin/bash

source config.sh

mkdir -p $DIR/data
BOOL=${1:-20}
DEPTH=${2:-8}
SEED=666

python3 generate.py -b "$BOOL" -d "$DEPTH" -s $SEED -o $DIR/data -m 10