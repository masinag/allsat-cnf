#!/usr/bin/env bash

# add option for with_repetition flag
run() {
  SCRIPT=$1
  DIR=$2
  RES_DIR=$3
  OTHER_OPT=("${@:4}")
  for dir in "$DIR"/data/*; do
    if [ -d "$dir" ]; then
        echo "$dir"
    fi
    res_dir="${dir//data/$RES_DIR}"
    mkdir -p "$res_dir"
    echo "$dir"
    for mode in NNF_MUTEX_POL LABELNEG_POL LAB; do
      python3 "$SCRIPT" "$dir" -m $mode -o "$res_dir" "${OTHER_OPT[@]}"
    done
  done
}

get-allsat() {
  run evaluate.py "$1" "results" "${@: 2}"
}

check-sat() {
  run evaluate.py "$1" "results-sat" "--sat" "${@: 2}"
}

run-d4() {
  # find D4_PATH environment variable
  if [ -z "$D4_PATH" ]; then
    echo "D4_PATH environment variable is not set"
    exit 1
  fi
  run evaluate_d4.py "${1}" "results-d4-${2}" --d4-mode="${2}" "${@: 3}" --d4-path "$D4_PATH"
}

run-tabularallsat() {
  if [ -z "$TABULARALLSAT_PATH" ]; then
    echo "TABULARALLSAT_PATH environment variable is not set"
    exit 1
  fi
  run evaluate_tabularallsat.py "${1}" "results-tabularallsat" "${@: 2}" --tabularallsat-path "$TABULARALLSAT_PATH"
}
