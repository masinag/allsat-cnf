#!/bin/bash

source config.sh

source generate.sh

source ../run-utils.sh

get-allsat $DIR
get-allsat $DIR --with-repetitions
