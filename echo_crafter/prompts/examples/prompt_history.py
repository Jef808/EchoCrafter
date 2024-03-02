#!/usr/bin/env python

import argparse
import json
import os
from pathlib import Path
import sys
import traceback
from rich.traceback import install

install()

LLM_API_HISTORY = f"{os.getenv('XDG_DATA_HOME')}/openai/new_logs.jsonl"


def format(content):
    """Extract text between backticks or return everything."""
    between_backticks = False
    results = []
    try:
        for line in map(lambda x: x.strip(), content.split('\n')):
            if line.startswith("```"):
                between_backticks = not between_backticks
                continue
            if between_backticks:
                results.append(line)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(formatted_traceback)
    return '\n'.join(results) if results else content


def print_entry(index, line):
    data = json.loads(line)
    language = data.get('language', '')
    timestamp = data.get('timestamp', 0)
    model = data.get('model', None)
    temperature = data.get('temperature', None)
    messages = data.get('messages', [])

    try:
        first_user_prompt = next(filter(lambda x: x['role'] == 'user', messages))
        first_assistant_response = next(filter(lambda x: x['role'] == 'user', messages))
    except StopIteration:
        return

    payload = {
        "index": index,
        "language": language,
        "timestamp": timestamp,
        "model": model,
        "temperature": temperature,
        "timestamp": timestamp,
        "query": format(first_user_prompt.get('content', '')),
        "answer": format(first_assistant_response.get('content', ''))
    }
    print(json.dumps(payload, indent=2))


def main():
    """Retrieve the queried history entries."""
    # Parse command line arguments
    if not Path(LLM_API_HISTORY).exists():
        print(f"LLM_API_HISTORY file not found: {LLM_API_HISTORY}", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('number', nargs='?', const=1, default=-5, type=int, help='Refers to event at index `number` if positive, else refers to event relative to the end of history')
    args = parser.parse_args()

    with open(LLM_API_HISTORY, 'r') as file:
        lines = file.readlines()

    if args.number < 0:
        lines = list(lines)
        number = max(0, len(lines) + args.number)
    else:
        number = args.number

    lines_to_print = (el for el in enumerate(lines) if el[0]+1 > number)
    for indexed_line in lines_to_print:
        print_entry(*indexed_line)


if __name__ == '__main__':
    main()
