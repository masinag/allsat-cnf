#!/bin/bash

DIR=aig-bench
DATA_URL=http://fmv.jku.at/aiger/smtqfbv-aigs.7z

# check if p7zip is installed
if ! which py7zr > /dev/null; then
    echo "py7zr not found: please install it by running 'pip install py7zr'"
    exit 1
fi

BOOL=$1
DEPTH=$2

REPETITIONS=""
TIMEOUT=600

archname=$(basename $DATA_URL)
dirname=$DIR/data/${archname%.*}


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
  py7zr x $tmpdata $dirname
  rm $tmpdata


fi


testdirname="$dirname-test"
if [ ! -d $testdirname ]; then
	mkdir $testdirname
	for f in $(ls $dirname | grep test); do
		ln -s $(realpath $dirname/$f) $testdirname/$f
	done
fi

mkdir -p $DIR/results $DIR/plots

for dir in $(ls -d $DIR/data/* | grep test); do
  res_dir=$(sed "s+data+results+g" <<<$dir)
  mkdir -p "$res_dir"
  echo $dir
  for mode in AUTO NNF_AUTO CND NNF_CND POL NNF_POL; do
    python3 ../evaluate.py "$dir" -m $mode -o "$res_dir" $REPETITIONS --timeout $TIMEOUT
  done
done

python3 ../plot.py $DIR/results/*b${BOOL}_d${DEPTH}* -o $DIR/plots
