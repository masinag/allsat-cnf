#!/usr/bin/env bash

source config.sh

python3 -m benchmark.generators.synthetic -b 0 -r 5 -d 5 -s $SEED -o $SYN_LRA_DIR/data -m 100
python3 -m benchmark.generators.synthetic -b 0 -r 5 -d 6 -s $SEED -o $SYN_LRA_DIR/data -m 100
python3 -m benchmark.generators.synthetic -b 0 -r 5 -d 7 -s $SEED -o $SYN_LRA_DIR/data -m 100
