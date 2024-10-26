#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${AIG_DIR}" enum
run-d4 "${AIG_DIR}" counting