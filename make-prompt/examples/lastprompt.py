#!/usr/bin/env python

import json
import os

LLM_API_HISTORY = f"{os.getenv('XDG_DATA_HOME')}/openai/logs.jsonl"


def format(content):
    between_backticks = False
    result = []
    for line in content.split('\n'):
        if between_backticks:
            result.append(line)
        else:
            between_backticks = not between_backticks
    return '\n'.join(result) if result else content


# read the last line of a jsonl file
with open(LLM_API_HISTORY, 'r') as f:
    last_line = list(f)[-1]

# convert the last line into json object
obj = json.loads(last_line)

# print the content
print(format(obj['responses'][0]['message']['content']))
