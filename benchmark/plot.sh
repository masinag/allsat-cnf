#!/bin/bash

source aig/config.sh
AIG_DIR=aig/$DIR

source iscas85/config.sh
ISCAS_DIR=iscas85/$DIR

source synthetic/config.sh
SYN_DIR=synthetic/$DIR

source wmi/config.sh
WMI_DIR=wmi/$DIR

echo $AIG_DIR $ISCAS_DIR $SYN_DIR $WMI_DIR

mkdir -p plots/bool/no-rep \
  plots/bool/rep \
  plots/lra/no-rep \
  plots/lra/rep \
  plots-sat/bool \
  plots-sat/lra

python3 plot.py \
  -problem_set syn-bool $SYN_DIR/results/*r0*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS_DIR/results/* \
  -o plots/bool/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra  $SYN_DIR/results/*b0*  \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/lra/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-bool $SYN_DIR/results/*r0*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS_DIR/results/* \
  -o plots/bool/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra  $SYN_DIR/results/*b0*  \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/lra/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000  \
  --scatter

# plot sat
python3 plot.py \
  -problem_set syn-bool $SYN_DIR/results-sat/*r0* \
  -problem_set aig      $AIG_DIR/results-sat/* \
  -problem_set iscas85  $ISCAS_DIR/results-sat/* \
  -o plots-sat/bool \
  --ecdf

python3 plot.py \
  -problem_set syn-lra  $SYN_DIR/results-sat/*b0* \
  -problem_set wmi      $WMI_DIR/results-sat/* \
  -o plots-sat/lra \
  --ecdf