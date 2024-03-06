#!/usr/bin/env python3

import sys
import json

def modify_timestamps_in_jsonl(file_path: str) -> None:
    """
    Modifies each entry in a JSONL (JSON Lines) file by converting its timestamp
    from a floating-point number to an integer by rounding.

    Args:
    file_path (str): The path to the JSONL file to be modified.
    """
    modified_lines = []
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            if 'timestamp' in data and isinstance(data['timestamp'], float):
                data['timestamp'] = round(data['timestamp'])
            modified_lines.append(json.dumps(data))

    with open(file_path, 'w') as file:
        for line in modified_lines:
            file.write(line + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python modify_timestamps_in_jsonl.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    modify_timestamps_in_jsonl(file_path)
