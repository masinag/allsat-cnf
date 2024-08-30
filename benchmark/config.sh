#!/usr/bin/env bash

export SEED=666

# ----- RESULTS DIRECTORIES -----
export RES_MSAT=results-msat
export RES_MSAT_SAT=results-msat-sat
export RES_D4_COUNTING=results-d4-counting
export RES_D4_PROJMC=results-d4-projmc
export RES_TABULARALLSAT=results-tabularallsat


# ----- PLOT DIRECTORIES -----
PLOT_MSAT=plot-msat
PLOT_MSAT_BOOL=${PLOT_MSAT}/bool
PLOT_MSAT_LRA=${PLOT_MSAT}/lra
PLOT_MSAT_SAT=${PLOT_MSAT}-sat
export PLOT_MSAT_SAT_BOOL=${PLOT_MSAT_SAT}/bool
export PLOT_MSAT_SAT_LRA=${PLOT_MSAT_SAT}/lra
export PLOT_MSAT_BOOL_REP=${PLOT_MSAT_BOOL}/rep
export PLOT_MSAT_BOOL_NO_REP=${PLOT_MSAT_BOOL}/no-rep
export PLOT_MSAT_LRA_REP=${PLOT_MSAT_LRA}/rep
export PLOT_MSAT_LRA_NO_REP=${PLOT_MSAT_LRA}/no-rep
export PLOT_D4_COUNTING=plot-d4-counting
export PLOT_D4_PROJMC=plot-d4-projmc
export PLOT_TABULARALLSAT=plot-tabularallsat

# ----- BENCHMARK DIRECTORIES -----
export AIG_DIR=aig-bench
export ISCAS85_DIR=iscas85-bench
export SYN_BOOL_DIR=syn-bool-bench
export SYN_LRA_DIR=syn-lra-bench
export WMI_DIR=wmi-bench

# ----- BENCHMARK NAMES -----
export AIG="aig"
export ISCAS85="iscas85"
export SYN_BOOL="syn-bool"
export SYN_LRA="syn-lra"
export WMI="wmi"

# ----- BENCHMARK EXECUTABLES -----
export D4_PATH=bin/d4
export TABULARALLSAT_PATH=bin/tabularallsat