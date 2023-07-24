#!/bin/bash

source config.sh

mkdir -p $DIR/plots/rep \
         $DIR/plots/no-rep \
         $DIR/plots-sat

#python3 ../plot.py $DIR/results/* -o $DIR/plots --timeout 1200 --timeout-models 1000000
python3 ../plot.py $DIR/results/* -o $DIR/plots/no-rep  --timeout 3600 --timeout-models 10000000
python3 ../plot.py $DIR/results/* -o $DIR/plots/rep --with-repetitions  --timeout 3600 --timeout-models 10000000

python3 ../plot.py $DIR/results-sat/* -o $DIR/plots-sat