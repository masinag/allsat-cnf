#!/bin/bash

#DIR=tip-aig-20061215
DIR=aig-bench
#DATA_URL=http://fmv.jku.at/aiger/tip-aig-20061215.zip
DATA_URL=http://fmv.jku.at/aiger/smtqfbv-aigs.7z

# check if p7zip is installed
if ! which 7zr > /dev/null; then
    echo "p7zip not found: please install it by running 'sudo apt-get install p7zip'"
    exit 1
fi

BOOL=$1
DEPTH=$2

REPETITIONS=""
archname=$(basename $DATA_URL)
dirname=$DIR/data/${dirname%.*}

# check if data DIR/data exists
if [ ! -d $dirname ]; then
  tmpdata=$DIR/tmp_data.7z
  # strip extension from filename
  mkdir -p $dirname
  echo "Data directory $dirname does not exist."
  echo "Downloading data from $DATA_URL..."
  wget -O $tmpdata $DATA_URL
  echo "Extracting data to $dirname..."
#  tar xzf $tmpdata -C $dirname
  7zr x $tmpdata -o$dirname
  rm $tmpdata
fi

mkdir -p $DIR/results $DIR/plots
echo $DIR/data
echo $(ls -d $DIR/data/* | grep test)
for dir in $(ls -d $DIR/data/* | grep test); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  echo $dir
  for mode in NNF_CND CND AUTO; do
    python3 evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS
  done
done

#python3 plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots
