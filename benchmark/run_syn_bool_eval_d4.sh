#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${SYN_BOOL_DIR}" counting
run-d4 "${SYN_BOOL_DIR}" projMC
run-d4 "${SYN_BOOL_DIR}" dDNNF