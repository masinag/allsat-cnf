#!/bin/bash

source config.sh

mkdir  $DIR/plots-sat -p $DIR/plots/no-rep $DIR/plots/rep

python3 ../plot.py $DIR/results-sat/* -o $DIR/plots-sat

python3 ../plot.py $DIR/results/*[^_REP] -o $DIR/plots/no-rep
python3 ../plot.py $DIR/results/*_REP -o $DIR/plots/rep --with-repetitions