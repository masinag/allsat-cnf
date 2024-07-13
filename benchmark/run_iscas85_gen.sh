#!/usr/bin/env bash

source config.sh

python3 -m benchmark.generators.iscas85 -o "{$ISCAS85_DIR}/data" -s "${SEED}"