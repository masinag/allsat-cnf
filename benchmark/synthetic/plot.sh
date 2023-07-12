#!/bin/bash

source config.sh

mkdir -p $DIR/plots-sat/bool \
        $DIR/plots-sat/lra \
         $DIR/plots/no-rep \
         $DIR/plots/rep \
         $DIR/plots/no-rep/bool \
         $DIR/plots/no-rep/lra \
         $DIR/plots/rep/bool \
          $DIR/plots/rep/lra

python3 ../plot.py $DIR/results/*r0* -o $DIR/plots/no-rep/bool --timeout 1200 --timeout-models 10000000
python3 ../plot.py $DIR/results/*r0* -o $DIR/plots/rep/bool --with-repetitions --timeout 1200 --timeout-models 10000000

python3 ../plot.py $DIR/results/*b0* -o $DIR/plots/no-rep/lra --timeout 1200 --timeout-models 10000000
python3 ../plot.py $DIR/results/*b0* -o $DIR/plots/rep/lra --with-repetitions --timeout 1200 --timeout-models 10000000

python3 ../plot.py $DIR/results-sat/*b0* -o $DIR/plots-sat/bool
python3 ../plot.py $DIR/results-sat/*r0* -o $DIR/plots-sat/lra