#!/bin/bash

mkdir -p $DIR/plots

python3 ../plot.py iscas85-bench/results/* -o iscas85-bench/plots --timeout 1200 --timeout-models 1000000