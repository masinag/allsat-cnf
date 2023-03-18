#!/bin/bash

DIR=iscas85-bench
DATA_FILE=files.txt
DATA_DIR=data

REPETITIONS=""

# benchmarks with more than 1 model
IFS=$'\n' read -d '' -r -a relevant_benchmarks <"small-benchmarks.txt"

# check if data DIR/data exists
if [ ! -d ${DATA_DIR}/ ]; then
  wget --directory-prefix=$DATA_DIR --input-file=$DATA_FILE
fi

mkdir -p $DIR/data $DIR/results $DIR/plots
for file in $(ls $DATA_DIR); do
  python3 generate.py $DATA_DIR/$file -o $DIR/data -m 5
done

for dir in $(ls -d $DIR/data/*); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  echo $dir
  for mode in LAB NNF_LAB CND NNF_CND NNF_POL POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS
  done
done

python3 ../plot.py iscas85-bench/results/* -o iscas85-bench/plots --timeout 1200 --timeout-models 1000000