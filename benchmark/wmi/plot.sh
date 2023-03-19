#!/bin/bash

source config.sh

mkdir -p $DIR/plots $DIR/plots-sat

python3 ../plot.py $DIR/results/* -o $DIR/plots

python3 ../plot.py $DIR/results-sat/* -o $DIR/plots-sat