#!/bin/bash

source config.sh

mkdir -p $DIR/plots

python3 ../plot.py $DIR/results/* -o $DIR/plots