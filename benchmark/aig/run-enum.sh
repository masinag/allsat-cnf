#!/bin/bash

source generate.sh

source ../run-utils.sh

get-allsat $DIR --timeout 3600
get-allsat $DIR --with-repetitions --timeout 3600