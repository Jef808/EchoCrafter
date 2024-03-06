#!/usr/bin/env zsh

#!/bin/zsh
# Script to replace specific strings in a given file

# Function to replace strings in a file
# Arguments:
#   $1: string - The file path
replace_strings() {
  local file_path=$1
  # Check if the file exists
  if [[ -f "$file_path" ]]; then
    # Use sed to replace "### Alice" with "**user**" and "### Bob" with "**assistant**"
    sed -i 's/### Alice/**user**/g' "$file_path"
    sed -i 's/### Bob/**assistant**/g' "$file_path"
    echo "Replacements done successfully."
  else
    echo "Error: File does not exist."
  fi
}

# Main script execution
# Check for the correct number of arguments
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <file_path>"
  exit 1
fi

# Call the replace_strings function with the provided file path
replace_strings $1