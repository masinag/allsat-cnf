#!/usr/bin/env bash

source config.sh

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

run-msat() {
  run evaluate_msat.py "$1" "${RES_MSAT}" "${@: 2}"
}

run-msat-sat() {
  run evaluate_msat.py "$1" "${RES_MSAT_SAT}" "--sat" "${@: 2}"
}

run-d4() {
  # find D4_PATH environment variable
  if [ -z "$D4_PATH" ]; then
    echo "D4_PATH environment variable is not set"
    exit 1
  fi
  # if $2 is "counting", then RES_D4 is RES_D4_COUNTING else if it is "projmc", then RES_D4 is RES_D4_PROJMC
  if [ "$2" == "counting" ]; then
    RES_D4="${RES_D4_COUNTING}"
  elif [ "$2" == "projMC" ]; then
    RES_D4="${RES_D4_PROJMC}"
  else
    echo "Invalid D4 mode: $2"
    exit 1
  fi

  run evaluate_d4.py "${1}" "$RES_D4" --d4-mode="${2}" "${@: 3}" --d4-path "$D4_PATH"
}

run-tabularallsat() {
  if [ -z "$TABULARALLSAT_PATH" ]; then
    echo "TABULARALLSAT_PATH environment variable is not set"
    exit 1
  fi
  run evaluate_tabularallsat.py "${1}" "${RES_TABULARALLSAT}" "${@: 2}" --tabularallsat-path "$TABULARALLSAT_PATH"
}
