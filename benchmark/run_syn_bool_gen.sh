#!/usr/bin/env bash

source config.sh

python3 -m benchmark.generators.synthetic -b 20 -r 0 -d 8 -s $SEED -o $SYN_BOOL_DIR/data -m 100
python3 -m benchmark.generators.synthetic -b 25 -r 0 -d 8 -s $SEED -o $SYN_BOOL_DIR/data -m 100
python3 -m benchmark.generators.synthetic -b 30 -r 0 -d 6 -s $SEED -o $SYN_BOOL_DIR/data -m 100
