#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-msat "${ISCAS85_DIR}" --timeout 3600
run-msat "${ISCAS85_DIR}" --with-repetitions --timeout 3600