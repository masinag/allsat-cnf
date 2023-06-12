#!/bin/bash

source config.sh

mkdir -p $DIR/plots $DIR/plots-sat

#python3 ../plot.py $DIR/results/* -o $DIR/plots --timeout 1200 --timeout-models 1000000
python3 ../plot.py $DIR/results/* -o $DIR/plots/no-rep  --timeout 1200 --timeout-models 1000000
python3 ../plot.py $DIR/results/* -o $DIR/plots/rep --with-repetitions  --timeout 1200 --timeout-models 1000000

python3 ../plot.py $DIR/results-sat/* -o $DIR/plots-sat