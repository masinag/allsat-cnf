#!/usr/bin/env bash

source config.sh

source run_utils.sh

get-allsat $ISCAS85_DIR --timeout 3600
get-allsat $ISCAS85_DIR --with-repetitions --timeout 3600