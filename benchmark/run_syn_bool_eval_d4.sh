#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-d4 "${SYN_BOOL_DIR}" enum
run-d4 "${SYN_BOOL_DIR}" counting
