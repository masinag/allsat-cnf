#!/bin/bash

source config.sh

SEED=666

MIN_DEPTH=4
MAX_DEPTH=7

for ((depth=$MIN_DEPTH; depth<=$MAX_DEPTH; depth++))
do
  python3 -m benchmark.generators.wmi -b 3 -r 3 -d $depth -o $WMI_DIR/data -n 10 --seed $SEED
done