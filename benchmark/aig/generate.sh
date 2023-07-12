#!/bin/bash

source config.sh

REPO_URL=https://github.com/yogevshalmon/allsat-circuits.git
DATA_DIR=data
BENCH_DIR=benchmarks

# check if data DIR/data exists
if [ ! -d ${DATA_DIR}/ ]; then
  # download directory from repo
  # source: https://stackoverflow.com/a/61470611
  mkdir $DATA_DIR
  cd $DATA_DIR
  git init
  git remote add origin $REPO_URL
  git config core.sparseCheckout true # enable sparse checkout
  echo "$BENCH_DIR/" >> .git/info/sparse-checkout # set the sparse checkout to the data directory
  git pull origin b57c2d6cba244460008dc6400beef2604a720c24
fi

# Expected structure:
# $DIR
# ├── data
# │   ├── random_aig_large_cir_or
# │   │   ├── bench1.aag
# │   │   ├── ...
# │   │   └── benchN.aag
# │   ├── sta_benchmarks
# │   │   ├── pi_9.aag
# │   │   ├── ...
# │   │   └── pi_129.aag
# │   ├── sta_benchmarks_large
# │   │   ├── pi_919.aag
# │   │   ├── ...
# │   │   └── 13009.aag
# │   ├── islis_benchmarks_arithmetic_or
# │   │   ├── adder.aag
# │   │   ├── ...
# │   │   └── square.aag
# │   ├── islis_benchmarks_arithmetic_xor
# │   │   ├── adder.aag
# │   │   ├── ...
# │   │   └── square.aag
# │   ├── islis_benchmarks_random_control_or
# │   │   ├── arbiter.aag
# │   │   ├── ...
# │   │   └── voter.aag
# │   └── islis_benchmarks_random_control_xor
# │       ├── arbiter.aag
# │       ├── ...
# │       └── voter.aag
# └── results
#

mkdir -p $DIR/data/random_aig_large_cir_or \
          $DIR/data/sta_benchmarks \
          $DIR/data/sta_benchmarks_large \
          $DIR/data/islis_benchmarks_arithmetic_or \
          $DIR/data/islis_benchmarks_arithmetic_xor \
          $DIR/data/islis_benchmarks_random_control_or \
          $DIR/data/islis_benchmarks_random_control_xor

cp $DATA_DIR/$BENCH_DIR/random_aig/large_cir_or/*/*.aag $DIR/data/random_aig_large_cir_or
cp $DATA_DIR/$BENCH_DIR/sta_benchmarks/*/*.aag $DIR/data/sta_benchmarks
cp $DATA_DIR/$BENCH_DIR/sta_benchmarks_large/*/*.aag $DIR/data/sta_benchmarks_large
cp $DATA_DIR/$BENCH_DIR/islis_benchmarks/arithmetic_or/*/*.aag $DIR/data/islis_benchmarks_arithmetic_or
cp $DATA_DIR/$BENCH_DIR/islis_benchmarks/arithmetic_xor/*/*.aag $DIR/data/islis_benchmarks_arithmetic_xor
cp $DATA_DIR/$BENCH_DIR/islis_benchmarks/random_control_or/*/*.aag $DIR/data/islis_benchmarks_random_control_or
cp $DATA_DIR/$BENCH_DIR/islis_benchmarks/random_control_xor/*/*.aag $DIR/data/islis_benchmarks_random_control_xor