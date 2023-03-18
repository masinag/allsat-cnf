#!/bin/bash

DIR=syn-bench
mkdir -p $DIR/data $DIR/results $DIR/plots
BOOL=$1
DEPTH=$2

REPETITIONS=""
NOXNNF=""

while getopts r:n: flag; do
  case "${flag}" in
  r) REPETITIONS="-r" ;;
  n) NOXNNF="--no-xnnf" ;;
  *)
    echo "Usage: $0 [-r] [-n]"
    exit 1
    ;;
  esac
done

python3 generate.py -b "$BOOL" -d "$DEPTH" -s 666 -o $DIR/data -m 10 $NOXNNF

for dir in $(ls -d $DIR/data/*b${BOOL}_d${DEPTH}*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  for mode in LAB NNF_MUTEX_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS
  done
done

#python3 ../plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots -f _${BOOL}_${DEPTH}
