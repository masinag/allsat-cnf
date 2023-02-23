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
  for mode in AUTO NNF_AUTO CND NNF_CND POL NNF_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir"
  done
done