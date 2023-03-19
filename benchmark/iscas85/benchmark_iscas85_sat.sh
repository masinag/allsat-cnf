#!/bin/bash

DIR=iscas85-bench

for dir in $(ls -d $DIR/data/*); do
  res_dir=$(sed "s+data+results-sat+g" <<<$dir)
  mkdir -p "$res_dir"
  echo $dir
  for mode in LAB POL NNF_POL NNF_MUTEX_POL LABELNEG_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" --sat
  done
done
