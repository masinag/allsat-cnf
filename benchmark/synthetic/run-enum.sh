#!/bin/bash

source config.sh

source generate.sh 20  0 8

source ../run-utils.sh

get-allsat $DIR
get-allsat $DIR --with-repetitions
