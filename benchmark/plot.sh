#!/bin/bash

source config.sh

echo "${AIG_DIR}" "${ISCAS85_DIR}" "${SYN_BOOL_DIR}" "${SYN_LRA_DIR}" "${WMI_DIR}"

mkdir -p plots/bool/no-rep \
  plots/bool/rep \
  plots/lra/no-rep \
  plots/lra/rep \
  plots-sat/bool \
  plots-sat/lra \
  plots-d4-counting \
  plots-d4-projMC \
  plots-tabularallsat

python3 plot.py \
  -problem_set syn-bool "${SYN_BOOL_DIR}"/results/* \
  -problem_set aig "${AIG_DIR}"/results/* \
  -problem_set iscas85 "${ISCAS85_DIR}"/results/* \
  -o plots/bool/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}"/results/* \
  -problem_set wmi "${WMI_DIR}"/results/* \
  -o plots/lra/no-rep \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-bool "${SYN_BOOL_DIR}"/results/* \
  -problem_set aig "${AIG_DIR}"/results/* \
  -problem_set iscas85 "${ISCAS85_DIR}"/results/* \
  -o plots/bool/rep \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  \
  -problem_set aig "${AIG_DIR}"/results-d4-projMC/* \
  -problem_set iscas85 "${ISCAS85_DIR}"/results-d4-projMC/* \
  -o plots-d4-projMC \
  --timeout 1200 --timeout-models 10000000000000 \
  --scatter \
  --time-only # -problem_set syn-bool "${SYN_BOOL_DIR}"/results-d4-projMC/* \

python3 plot.py \
  \
  -problem_set aig "${AIG_DIR}"/results-d4-counting/* \
  -problem_set iscas85 "${ISCAS85_DIR}"/results-d4-counting/* \
  -o plots-d4-counting \
  --timeout 1200 --timeout-models 10000000000000 \
  --scatter \
  --time-only # -problem_set syn-bool "${SYN_BOOL_DIR}"/results-d4-dDNNF/* \

plot.py \
  -problem_set syn-bool "${SYN_BOOL_DIR}"/results-tabularallsat/* \
  -problem_set aig "${AIG_DIR}"/results-tabularallsat/* \
  -problem_set iscas85 "${ISCAS85_DIR}"/results-tabularallsat/* \
  -o plots-tabularallsat \
  --timeout 1200 --timeout-models 10000000000000 \
  --scatter