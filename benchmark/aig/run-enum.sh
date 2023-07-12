#!/bin/bash

source generate.sh

source ../run-utils.sh

get-allsat $DIR
get-allsat $DIR --with-repetitions