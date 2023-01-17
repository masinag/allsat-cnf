#!/usr/bin/bash

# Remove carriage returns from aag files
# Usage: remove_cr.sh <file>

# Check for file
if [ -z "$1" ]; then
    echo "Usage: remove_cr.sh <file>"
    exit 1
fi

# Replace carriage returns with newlines
sed -i "$1" 's/\r//g'