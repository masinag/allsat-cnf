#!/bin/bash

source config.sh

mkdir -p $DIR/data

BOOL=10
DEPTHS="3 5 7 9"
N=10

for DEPTH in $DEPTHS; do
  python3 generate.py -b "$BOOL" -r 0 -d "$DEPTH" -s 666 -o $DIR/data -n $N
done
