#!/bin/bash

source config.sh

source generate.sh

source ../run-utils.sh

check-sat $DIR
