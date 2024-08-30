#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-msat "${SYN_LRA_DIR}" --timeout 3600
run-msat "${SYN_LRA_DIR}" --with-repetitions --timeout 3600