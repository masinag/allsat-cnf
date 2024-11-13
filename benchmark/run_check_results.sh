#!/usr/bin/env bash

check_results() {
    dir=$1
    echo "Checking results in $dir"
    # Use find with -exec to call the Python script directly with all files as arguments
    find "$dir" -type d -name 'results*' \
     ! -name 'results-msat-sat' \
     -exec python3 check_results.py {} +
}

# Call the function with different directories
check_results "aig-bench"
check_results "syn-bool-bench"
check_results "iscas85-bench"