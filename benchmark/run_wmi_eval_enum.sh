#!/usr/bin/env bash

source config.sh

source run_utils.sh

get-allsat $WMI_DIR --timeout 3600
get-allsat $WMI_DIR --with-repetitions --timeout 3600