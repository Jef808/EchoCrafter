#!/usr/bin/env python3

import sys
import json
from typing import Union, Dict, Any

def convert_jsonl(input_file: str, output_file: str) -> None:
    """
    Convert each entry in a JSONL file to a specific object format.
    
    This function reads a JSONL file where each entry is a key-value pair. The keys are either 'null' or the string representation of a floating point number.
    It converts these entries into objects of the form {timestamp: <timestamp>, summary: <summary>}, where <timestamp> is the closest integer to the floating point number (or 'null') and <summary> is the original value of the key-value pair.
    The results are written to a new JSONL file.
    
    Args:
        input_file (str): The path to the input JSONL file.
        output_file (str): The path to the output JSONL file.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            entry = json.loads(line)
            key, value = next(iter(entry.items()))
            timestamp = round(float(key)) if key != 'null' else None
            new_entry = {"timestamp": timestamp, "summary": value.replace('Alice', 'user').replace('Bob', 'assistant')}
            json.dump(new_entry, outfile)
            outfile.write('\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_jsonl.py <input_file> <output_file>")
        sys.exit(1)
    input_file, output_file = sys.argv[1], sys.argv[2]
    convert_jsonl(input_file, output_file)
