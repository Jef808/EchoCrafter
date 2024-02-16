#!/usr/bin/env python
import argparse
import json

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('q', '--query', action='store_true', help='output only query fields')
parser.add_argument('a', '--answer', action='store_true', help='output only answer fields')
parser.add_argument('n', '--number', type=int, default=5, help='select the number of entries to output')
parser.add_argument('i', '--index', type=int, help='select the index of the entry to output')
args = parser.parse_args()

log_file = "/home/jfa/.local/share/openai/logs.jsonl"

with open(log_file, 'r') as file:
    i = args.get('index') or 0
    n = args.number
    number = max(i, n)
    lines = file.readlines()[-number:]
    if args.index is not None:
        lines = [lines[-1 * args.index]]

for line in lines:
    data = json.loads(line)
    messages = data['payload']['messages']
    responses = data['responses']
    timestamp = data['timestamp']
    user_prompt = [message['content'] for message in messages if message['role'] == 'user'][-1]
    assistant_response = [response['message']['content'] for response in responses if response['message']['role'] == 'assistant'][-1]
    payload = {
        "timestamp": timestamp,
        "query": user_prompt,
        "answer": assistant_response
    }
    if args.query:
        print(json.dumps({"timestamp": timestamp, "query": user_prompt}))
    elif args.answer:
        print(json.dumps({"timestamp": timestamp, "answer": assistant_response}))
    else:
        print(json.dumps(payload))
