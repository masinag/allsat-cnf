#!/bin/bash

DIR=wmi-bench
mkdir -p $DIR/data $DIR/results $DIR/plots
BOOL=10
DEPTHS="3 5 7 9"
N=10

for DEPTH in $DEPTHS; do
  python3 generate.py -b "$BOOL" -r 0 -d "$DEPTH" -s 666 -o $DIR/data -n $N
done

for dir in $(ls -d $DIR/data/*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  for mode in LAB POL NNF_POL NNF_MUTEX_POL LABELNEG_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir"
  done
done

python3 ../plot.py wmi-bench/results/models_b10_r0_d* -o wmi-bench/plots