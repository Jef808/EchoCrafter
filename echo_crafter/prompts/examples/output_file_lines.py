#!/usr/bin/env python3

import sys

def output_file_lines(filename: str, start_line: int, end_line: int) -> None:
    """
    Outputs specified lines from a file.

    Args:
    filename (str): The path to the file.
    start_line (int): The first line to output (1-indexed).
    end_line (int): The last line to output (inclusive).

    Returns:
    None: This function prints the specified lines to stdout.
    """
    try:
        with open(filename, 'r') as file:
            for current_line_number, line in enumerate(file, start=1):
                if start_line <= current_line_number <= end_line:
                    print(line, end='')
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python output_file_lines.py <filename> <start_line> <end_line>")
        sys.exit(1)

    filename_arg = sys.argv[1]
    start_line_arg = int(sys.argv[2])
    end_line_arg = int(sys.argv[3])

    output_file_lines(filename_arg, start_line_arg, end_line_arg)