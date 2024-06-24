#!/bin/bash

source config.sh

echo $AIG_DIR $ISCAS85_DIR $SYN_BOOL_DIR $SYN_LRA_DIR $WMI_DIR

mkdir -p plots/bool/no-rep \
  plots/bool/rep \
  plots/lra/no-rep \
  plots/lra/rep \
  plots-sat/bool \
  plots-sat/lra

python3 plot.py \
  -problem_set syn-bool $SYN_BOOL_DIR/results/*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS85_DIR/results/* \
  -o plots/bool/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra  $SYN_LRA_DIR/results/*  \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/lra/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-bool $SYN_BOOL_DIR/results/*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS85_DIR/results/* \
  -o plots/bool/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra  $SYN_LRA_DIR/results/*  \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/lra/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000  \
  --scatter

# plot sat
python3 plot.py \
  -problem_set syn-bool $SYN_BOOL_DIR/results-sat/* \
  -problem_set aig      $AIG_DIR/results-sat/* \
  -problem_set iscas85  $ISCAS85_DIR/results-sat/* \
  -o plots-sat/bool \
  --ecdf

python3 plot.py \
  -problem_set syn-lra  $SYN_LRA_DIR/results-sat/* \
  -problem_set wmi      $WMI_DIR/results-sat/* \
  -o plots-sat/lra \
  --ecdf