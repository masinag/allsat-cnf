#!/bin/bash

DIR=syn-bench
BOOL=$1
DEPTH=$2

for dir in $(ls -d $DIR/data/*b${BOOL}_d${DEPTH}*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  for mode in LAB POL NNF_POL NNF_MUTEX_POL LABELNEG_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" --sat
  done
done

#python3 ../plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots -f _${BOOL}_${DEPTH}
