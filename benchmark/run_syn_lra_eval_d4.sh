#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${SYN_LRA_DIR}" counting
run-d4 "${SYN_LRA_DIR}" projMC
run-d4 "${SYN_LRA_DIR}" dDNNF