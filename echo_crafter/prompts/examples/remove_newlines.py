#!/usr/bin/env python3
import sys
import re

def remove_newlines_except_braces(file_path: str) -> None:
    """
    Removes all newline characters in a file except those immediately surrounded by '}' and '{'.
    
    Args:
    file_path (str): The path to the file to be processed.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace newlines not surrounded by '}' and '{' with empty string
    modified_content = re.sub(r'(?<!\})\n(?!\{)', '', content)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python remove_newlines.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    remove_newlines_except_braces(file_path)
