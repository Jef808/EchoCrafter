#!/usr/bin/env zsh

#!/bin/zsh
# Script to add a "summary" field with an empty string value to each entry in a .jsonl file that does not already have a "summary" field.

# Function to process a .jsonl file and add missing "summary" fields.
process_jsonl_file() {
  local input_file=$1
  local output_file="${input_file%.jsonl}_processed.jsonl"

  # Check if the input file exists
  if [[ ! -f "$input_file" ]]; then
    echo "Error: File '$input_file' does not exist."
    exit 1
  fi

  # Process each line of the input file
  while IFS= read -r line; do
    # Check if the line contains a "summary" field
    if echo "$line" | grep -q '"summary":'; then
      # If it does, write the line unchanged to the output file
      echo "$line" >> "$output_file"
    else
      # If it does not, add a "summary" field with an empty string value
      # Assumes the JSON line ends with a closing brace }
      modified_line=$(echo "$line" | sed 's/}$/,"summary":""}/')
      echo "$modified_line" >> "$output_file"
    fi
  done < "$input_file"

  echo "Processed file saved as '$output_file'."
}

# Main script execution
# Check for correct usage
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <input_file.jsonl>"
  exit 1
fi

input_file=$1
process_jsonl_file "$input_file"