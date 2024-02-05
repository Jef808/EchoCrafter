#!/home/jfa/projects/echo-crafter/.venv/bin/python

import argparse
import subprocess
import json
import os
from pathlib import Path
from openai import OpenAI

DEFAULT_MODEL = "gpt-4"
DEFAULT_LOG_FILE = Path(os.getenv("XDG_DATA_HOME")) / "openai/logs.jsonl"


def make_payload(args, prompt):
    """Make the payload for the OpenAI API."""
    system_prompt = ("carefully analyze the intent of the provided command "
                     "then replace it with a python script which, when executed, will run that command")
    example = [{"role": "system", "name": "example_user", "content": "```\ngive me the absolute path to my home directory\n```"},
               {"role": "system", "name": "example_assistant", "content": "```python\nimport os;\nprint(os.getenv('HOME'))\n```"}]
    payload = {
        "model": args.model,
        "stop": "\n```",
        "messages": [
            {"role": "system", "content": system_prompt}
        ]
    }
    payload['messages'].extend(example)
    payload['messages'].append({"role": "user", "content": f"```\n{prompt.strip()}\n```"})
    return payload


def get_api_key():
    """Get the OpenAI API key from the password store."""
    api_key = subprocess.check_output(["pass", "openai.com/api_key"])
    api_key = str(api_key, encoding="utf-8").rstrip()
    return api_key


def format_response(content):
    """Extract the response from the content."""
    result = []
    between_backticks = False
    for line in content.split('\n'):
        if line.strip().startswith("```"):
            between_backticks = not between_backticks
            continue
        if between_backticks:
            result.append(line)
    response = '\n'.join(result) if result else content
    return response


def log(payload, response, log_file=DEFAULT_LOG_FILE):
    """Log the payload and response to a file."""
    log_entry = {
        "language": "python",
        "timestamp": response['created'],
        "model": response['model'],
        "payload": payload,
        "responses": response['choices'],
        "usage": response['usage']
    }
    with open(log_file, 'a+') as f:
        f.write(json.dumps(log_entry) + '\n')


def main():
    """Run the main program."""
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=DEFAULT_MODEL)
    parser.add_argument('command', nargs='?', help='Optional command')
    args = parser.parse_args()

    command = args.command
    if command is None:
        command = input()

    openai_client = OpenAI(api_key=get_api_key())

    payload = make_payload(args, command)

    response = openai_client.chat.completions.create(**payload)
    py_response = response.model_dump()

    log(payload, py_response)

    content = py_response['choices'][0]['message']['content']

    print(format_response(content))


if __name__ == '__main__':
    main()
