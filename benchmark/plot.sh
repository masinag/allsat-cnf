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

mkdir -p plots/no-rep plots/rep

python3 plot.py \
  -problem_set syn-bool $SYN_DIR/results/*r0*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS_DIR/results/* \
  -problem_set syn-lra  $SYN_DIR/results/* \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/no-rep \
  --timeout 3600 --timeout-models 100000000

python3 plot.py \
  -problem_set syn-bool $SYN_DIR/results/*r0*  \
  -problem_set aig      $AIG_DIR/results/* \
  -problem_set iscas85  $ISCAS_DIR/results/* \
  -problem_set syn-lra  $SYN_DIR/results/* \
  -problem_set wmi      $WMI_DIR/results/* \
  -o plots/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000
