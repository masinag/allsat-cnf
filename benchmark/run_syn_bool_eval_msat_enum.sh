#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-msat "${SYN_BOOL_DIR}" --timeout 3600
run-msat "${SYN_BOOL_DIR}" --with-repetitions --timeout 3600