#!/bin/bash

source config.sh

mkdir -p $DIR/plots-sat $DIR/plots/no-rep $DIR/plots/rep

python3 ../plot.py $DIR/results/*b20* -o $DIR/plots/no-rep --timeout 1200 --timeout-models 10000000
python3 ../plot.py $DIR/results/*b20* -o $DIR/plots/rep --with-repetitions --timeout 1200 --timeout-models 10000000


python3 ../plot.py $DIR/results-sat/* -o $DIR/plots-sat