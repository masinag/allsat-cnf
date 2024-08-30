#!/usr/bin/env bash

source config.sh

source run_utils.sh

run-msat "${WMI_DIR}" --timeout 3600
run-msat "${WMI_DIR}" --with-repetitions --timeout 3600