#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${ISCAS85_DIR}" counting
run-d4 "${ISCAS85_DIR}" projMC
run-d4 "${ISCAS85_DIR}" dDNNF