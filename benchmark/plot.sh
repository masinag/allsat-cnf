#!/bin/bash

source config.sh

echo "${AIG_DIR}" "${ISCAS85_DIR}" "${SYN_BOOL_DIR}" "${SYN_LRA_DIR}" "${WMI_DIR}"

mkdir -p \
  "${PLOT_MSAT_SAT_BOOL}" \
  "${PLOT_MSAT_SAT_LRA}" \
  "${PLOT_MSAT_BOOL_REP}" \
  "${PLOT_MSAT_BOOL_NO_REP}" \
  "${PLOT_MSAT_LRA_REP}" \
  "${PLOT_MSAT_LRA_NO_REP}" \
  "${PLOT_D4_COUNTING}" \
  "${PLOT_D4_PROJMC}" \
  "${PLOT_TABULARALLSAT}"

python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_MSAT}/*" \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_MSAT}/*" \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_MSAT}/*" \
  -o "${PLOT_MSAT_BOOL_NO_REP}" \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}/${RES_MSAT}/*" \
  -problem_set wmi "${WMI_DIR}/${RES_MSAT}/*" \
  -o "${PLOT_MSAT_LRA_NO_REP}" \
  --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_MSAT}/*" \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_MSAT}/*" \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_MSAT}/*" \
  -o "${PLOT_MSAT_BOOL_REP}" \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}/${RES_MSAT}/*" \
  -problem_set wmi "${WMI_DIR}/${RES_MSAT}/*" \
  -o "${PLOT_MSAT_LRA_REP}" \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter

python3 plot.py \
  \
  -problem_set "${AIG}" "${AIG_DIR}"/results-d4-projMC/* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}"/results-d4-projMC/* \
  -o "${PLOT_D4_PROJMC}" \
  --timeout 1200 --timeout-models 10000000000000 \
  --scatter \
  --time-only # -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}"/results-d4-projMC/* \

python3 plot.py \
  \
  -problem_set "${AIG}" "${AIG_DIR}"/results-d4-counting/* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}"/results-d4-counting/* \
  -o "${PLOT_D4_COUNTING}" \
  --timeout 1200 --timeout-models 10000000000000 \
  --scatter \
  --time-only # -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}"/results-d4-dDNNF/* \

python3 plot.py \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}"/results-tabularallsat/* \
  -o "${PLOT_TABULARALLSAT}" \
  --timeout 3600 --timeout-models 10000000000000 \
  --scatter
#  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}"/results-tabularallsat/* \
#  -problem_set "${AIG}" "${AIG_DIR}"/results-tabularallsat/* \
