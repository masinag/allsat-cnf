#!/bin/bash

DIR=aig-bench
DATA_URL=http://fmv.jku.at/aiger/smtqfbv-aigs.7z

# check if p7zip is installed
if ! which py7zr >/dev/null; then
  echo "py7zr not found: please install it by running 'pip install py7zr'"
  exit 1
fi

REPETITIONS=""
TIMEOUT=600

archname=$(basename $DATA_URL)
dirname=$DIR/data/${archname%.*}
# benchmarks with more than 1 model
IFS=$'\n' read -d '' -r -a relevant_benchmarks <"small-benchmarks.txt"

# check if data DIR/data exists
if [ ! -d $dirname ]; then
  tmpdata=$DIR/tmp_data.7z
  # strip extension from filename
  mkdir -p $dirname
  echo "Data directory $dirname does not exist."
  echo "Downloading data from $DATA_URL..."
  wget -O $tmpdata $DATA_URL
  echo "Extracting data to $dirname..."
  py7zr x $tmpdata $dirname
  rm $tmpdata

fi

relevant_benchmarks_dirname="$dirname-small"
if [ ! -d $relevant_benchmarks_dirname ]; then
  mkdir $relevant_benchmarks_dirname
  for f in $(ls $dirname | grep test); do
    # shellcheck disable=SC2076
    if [[ " ${relevant_benchmarks[*]} " =~ " ${f} " ]]; then
      ln -s $(realpath $dirname/$f) $relevant_benchmarks_dirname/$f
    fi
  done
fi


mkdir -p $DIR/results $DIR/plots

for dir in $(ls -d $DIR/data/* | grep small); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  echo $dir
  for mode in LAB NNF_LAB CND NNF_CND NNF_POL POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS --timeout $TIMEOUT
  done
done

python3 ../plot.py $DIR/results/*test* -o $DIR/plots
