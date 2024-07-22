#!/bin/bash
# Function to process JSON files and add timestamp field
process_json_file() {
  local json_file="$1"
  local timestamp="$2"

  python3 - <<EOF
import json
from datetime import datetime

timestamp = $timestamp
datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
print("Timestamp:", datetime_str)
with open("$json_file", 'r') as file:
    data = json.load(file)

for result in data.get('results', []):
    result['timestamp'] = datetime_str

with open("$json_file", 'w') as file:
    json.dump(data, file, indent=4)
EOF
}

find . -type f -name "*.json" | while read -r file; do
  # Extract the directory and filename without extension
  dir=$(dirname "$file")
  filename=$(basename "$file")

  # Extract the timestamp part (last part of the filename without extension)
  timestamp=$(echo "$filename" | rev | cut -d'_' -f1 | rev | cut -d'.' -f1)

  # Get the problem_set and mode by stripping the timestamp
  base_name=$(echo "$filename" | sed "s/_${timestamp}\.json$//")

  # Rename the file
  new_filename="${base_name}.json"
  new_filepath="${dir}/${new_filename}"

  echo "Renaming $file to $new_filepath"
  # Process the JSON file to add the timestamp field
  process_json_file "$file" "$timestamp"

  # Rename the file
   mv "$file" "$new_filepath"

done
