#!/bin/bash

DIR=tip-aig-20061215
mkdir -p $DIR/data $DIR/results $DIR/plots
BOOL=$1
DEPTH=$2

REPETITIONS=""
NOXNNF=""


for dir in $(ls -d $DIR/data/*b${BOOL}_d${DEPTH}*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  for mode in NNF_CND CND AUTO; do
    python3 evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS
  done
done

#python3 plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots
