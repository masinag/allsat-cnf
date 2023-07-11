#!/bin/bash

source config.sh

# BOOL
source generate.sh 20  0 8
source generate.sh 25  0 8
source generate.sh 30  0 6
# LRA
source generate.sh  0  5 5
source generate.sh  0  5 6
source generate.sh  0  5 7

source ../run-utils.sh

get-allsat $DIR
get-allsat $DIR --with-repetitions
