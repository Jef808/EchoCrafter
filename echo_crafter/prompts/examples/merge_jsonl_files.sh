#!/usr/bin/env zsh

#!/bin/zsh
# merge_jsonl.sh
#
# Description: Merges two '.jsonl' files based on the criteria that a line from the second file
# either inserts or overwrites a line in the first file if it completely supersedes it but has one additional field.

# Function to merge two '.jsonl' files based on the specified criteria.
# Arguments:
#   $1: Path to the first '.jsonl' file.
#   $2: Path to the second '.jsonl' file.
# Outputs:
#   Writes the merged content to the first '.jsonl' file.
merge_jsonl_files() {
    local file1=$1
    local file2=$2

    # Temporary file to store the merged results.
    local temp_file=$(mktemp)

    # Read each line from the second file.
    while IFS= read -r line2; do
        local found=0
        # Convert JSON line to a comparable string (sorted keys, removed spaces).
        local comp_line2=$(echo $line2 | jq -c --sort-keys .)

        # Read each line from the first file to compare.
        while IFS= read -r line1; do
            local comp_line1=$(echo $line1 | jq -c --sort-keys .)

            # Check if the lines are equal or if line2 supersedes line1 with one additional field.
            if [[ $comp_line1 == $comp_line2 ]]; then
                found=1
                break
            else
                # Count fields in both lines.
                local count_line1=$(echo $comp_line1 | jq 'length')
                local count_line2=$(echo $comp_line2 | jq 'length')

                # If line2 has exactly one more field and all other fields match, it supersedes line1.
                if (( count_line2 == count_line1 + 1 )) && echo $comp_line2 | jq --argjson line1 "$comp_line1" 'all(has(.key); .key != "additionalField")'; then
                    found=1
                    break
                fi
            fi
        done < "$file1"

        # If line2 was not found or did not supersede any line in file1, append it to the temp file.
        if [[ $found -eq 0 ]]; then
            echo $line2 >> "$temp_file"
        fi
    done < "$file2"

    # Append the original content of file1 to the temp file.
    cat "$file1" >> "$temp_file"

    # Replace the original file1 with the merged results.
    mv "$temp_file" "$file1"
}

# Check if the correct number of arguments is provided.
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <path_to_first_jsonl_file> <path_to_second_jsonl_file>"
    exit 1
fi

# Call the merge function with the provided file paths.
merge_jsonl_files "$1" "$2"