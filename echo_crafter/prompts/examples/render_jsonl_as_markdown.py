#!/usr/bin/env python3

import sys
import json
from typing import List, Dict

def render_jsonl_as_markdown(jsonl_file_path: str, output_file_path: str) -> None:
    """
    Renders a JSONL file consisting of key-value pairs, where the values are markdown strings,
    into a markdown file for easy parsing.

    Args:
    - jsonl_file_path (str): The path to the input JSONL file.
    - output_file_path (str): The path to the output markdown file.
    """
    with open(jsonl_file_path, 'r') as jsonl_file, open(output_file_path, 'w') as md_file:
        for line in jsonl_file:
            record = json.loads(line)
            for key, value in record.items():
                md_file.write(f"## {key}\n{value}\n\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python render_jsonl_as_markdown.py <input_jsonl_file_path> <output_markdown_file_path>")
        sys.exit(1)
    input_jsonl_file_path = sys.argv[1]
    output_markdown_file_path = sys.argv[2]
    render_jsonl_as_markdown(input_jsonl_file_path, output_markdown_file_path)
