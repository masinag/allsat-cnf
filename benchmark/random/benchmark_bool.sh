#!/bin/bash

DIR=bool_bench
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

python3 generate_bool.py -b "$BOOL" -d "$DEPTH" -s 666 -o $DIR/data -m 100 $REPETITIONS $NOXNNF

for dir in $(ls -d $DIR/data/*b${BOOL}_d${DEPTH}*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  for mode in NNF_CND CND AUTO; do
    python3 evaluate.py "$dir" -m $mode -o "$res_dir"
  done
done

python3 plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots
