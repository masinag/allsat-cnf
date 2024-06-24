#!/usr/bin/env bash

source config.sh

source run_utils.sh

get-allsat $SYN_BOOL_DIR --timeout 3600
get-allsat $SYN_BOOL_DIR --with-repetitions --timeout 3600