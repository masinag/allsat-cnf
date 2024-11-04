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
  "${PLOT_D4_ENUM}" \
  "${PLOT_TABULARALLSAT}" \
  "${PLOT_TABULARALLSMT}"


echo "Plotting ${PLOT_MSAT_SAT_BOOL}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_MSAT_SAT}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_MSAT_SAT}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_MSAT_SAT}/"* \
  -o "${PLOT_MSAT_SAT_BOOL}" \
  --ecdf


echo "Plotting ${PLOT_MSAT_SAT_LRA}..."
python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}/${RES_MSAT_SAT}/"* \
  -problem_set wmi "${WMI_DIR}/${RES_MSAT_SAT}/"* \
  -o "${PLOT_MSAT_SAT_LRA}" \
  --ecdf


echo "Plotting ${PLOT_MSAT_BOOL_NO_REP}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_MSAT}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_MSAT}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_MSAT}/"* \
  -o "${PLOT_MSAT_BOOL_NO_REP}" \
  --timeout 3600 --timeout-models 100000000 \
  --scatter


echo "Plotting ${PLOT_MSAT_LRA_NO_REP}..."
python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}/${RES_MSAT}/"* \
  -problem_set wmi "${WMI_DIR}/${RES_MSAT}/"* \
  -o "${PLOT_MSAT_LRA_NO_REP}" \
  --timeout 3600 --timeout-models 100000000 \
  --scatter


echo "Plotting ${PLOT_MSAT_BOOL_REP}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_MSAT}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_MSAT}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_MSAT}/"* \
  -o "${PLOT_MSAT_BOOL_REP}" \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter


echo "Plotting ${PLOT_MSAT_LRA_REP}..."
python3 plot.py \
  -problem_set syn-lra "${SYN_LRA_DIR}/${RES_MSAT}/"* \
  -problem_set wmi "${WMI_DIR}/${RES_MSAT}/"* \
  -o "${PLOT_MSAT_LRA_REP}" \
  --with-repetitions --timeout 3600 --timeout-models 100000000 \
  --scatter


echo "Plotting ${PLOT_TABULARALLSAT}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_TABULARALLSAT}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_TABULARALLSAT}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_TABULARALLSAT}/"* \
  -o "${PLOT_TABULARALLSAT}" \
  --timeout 3600 --timeout-models 10000000000 \
  --scatter


echo "Plotting ${PLOT_TABULARALLSMT}..."
python3 plot.py \
  -problem_set "${SYN_LRA}" "${SYN_LRA_DIR}/${RES_TABULARALLSMT}/"* \
  -problem_set "${WMI}" "${WMI_DIR}/${RES_TABULARALLSMT}/"* \
  -o "${PLOT_TABULARALLSMT}" \
  --timeout 3600 --timeout-models 100000 \
  --scatter


echo "Plotting ${PLOT_D4_ENUM}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_D4_ENUM}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_D4_ENUM}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_D4_ENUM}/"* \
  -o "${PLOT_D4_ENUM}" \
  --timeout 3600 --timeout-models 1000000000 \
  --scatter


echo "Plotting ${PLOT_D4_COUNTING}..."
python3 plot.py \
  -problem_set "${SYN_BOOL}" "${SYN_BOOL_DIR}/${RES_D4_COUNTING}/"* \
  -problem_set "${ISCAS85}" "${ISCAS85_DIR}/${RES_D4_COUNTING}/"* \
  -problem_set "${AIG}" "${AIG_DIR}/${RES_D4_COUNTING}/"* \
  -o "${PLOT_D4_COUNTING}" \
  --timeout 3600 --timeout-models 1000000000000 \
  --scatter \
  --time-only