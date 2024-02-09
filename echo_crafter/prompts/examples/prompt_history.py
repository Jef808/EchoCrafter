#!/usr/bin/env python

import argparse
import json
import os
from pathlib import Path
import sys

LLM_API_HISTORY = f"{os.getenv('XDG_DATA_HOME')}/openai/logs.jsonl"


def format(content):
    """Extract text between backticks or return everything."""
    between_backticks = False
    results = []
    for line in map(lambda x: x.strip(), content.split('\n')):
        if line.startswith("```"):
            between_backticks = not between_backticks
            continue
        if between_backticks:
            results.append(line)
    return '\n'.join(results) if results else content


def print_entry(index, line):
    """Print the entry at index `index`."""
    data = json.loads(line)
    messages = data['payload']['messages']
    responses = data['responses']
    timestamp = data['timestamp']
    last_user_prompt = [message['content'] for message in messages if message['role'] == 'user'][-1]
    last_assistant_response = [response['message']['content'] for response in responses if response['message']['role'] == 'assistant'][-1]
    payload = {
        "index": index,
        "timestamp": timestamp,
        "query": format(last_user_prompt),
        "answer": format(last_assistant_response)
    }
    print(json.dumps(payload, indent=2))


def main():
    """Retrieve the queried history entries."""
    if not Path(LLM_API_HISTORY).exists():
        print(f"LLM_API_HISTORY file not found: {LLM_API_HISTORY}", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'number',
        nargs='?',
        const=1,
        default=-5,
        type=int,
        help='Refers to event at index `number` if positive, else refers to event relative to the end of history'
    )
    parser.add_argument(
        '-r',
        '--raw',
        action='store_true',
        help='Print the raw content of the last `number` events'
    )
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
