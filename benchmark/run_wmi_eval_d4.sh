#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${WMI_DIR}" counting
run-d4 "${WMI_DIR}" projMC
run-d4 "${WMI_DIR}" dDNNF