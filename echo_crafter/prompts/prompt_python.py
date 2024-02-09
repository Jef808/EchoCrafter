#!/home/jfa/projects/echo-crafter/.venv/bin/python

from echo_crafter.prompts.utils import try_extract_from_backticks, get_openai_api_key

import json
import os
from pathlib import Path
from openai import OpenAI, OpenAIError
import traceback
import sys

DEFAULT_MODEL = "gpt-4"
DEFAULT_LOG_FILE = Path(os.getenv("XDG_DATA_HOME")) / "openai/logs.jsonl"


def make_payload(command, *, history, model):
    """Make the payload for the OpenAI API."""
    system_prompt = ("carefully analyze the intent of the provided command "
                     "then replace it with a python script which, when executed, will run that command")
    example = [{"role": "system", "name": "example_user", "content": "```\ngive me the absolute path to my home directory\n```"},
               {"role": "system", "name": "example_assistant", "content": "```python\nimport os;\nprint(os.getenv('HOME'))\n```"}]
    payload = {
        "model": model,
        "stop": "\n```\n",
        "messages": [
            {"role": "system", "content": system_prompt}
        ]
    }
    payload['messages'].extend(example if not history else history)
    payload['messages'].append({"role": "user", "content": f"```\n{command}\n```"})
    return payload


def log(payload, response, log_file=DEFAULT_LOG_FILE):
    """Log the payload and response to a file."""
    _response = response.model_dump()
    log_entry = {
        "language": "python",
        "timestamp": _response['created'],
        "model": _response['model'],
        "payload": payload,
        "responses": _response['choices'],
        "usage": _response['usage']
    }
    with open(log_file, 'a+') as f:
        f.write(json.dumps(log_entry) + '\n')


def main(command, *, history=[], model=DEFAULT_MODEL):
    """
    Ask OpenAI's `model` to generate a shell script according to `command`.

    Returns OpenAI's full response object.
    """
    openai_client = OpenAI(api_key=get_openai_api_key())
    payload = make_payload(command, history=history, model=model)

    response = openai_client.chat.completions.create(**payload)
    log(payload, response)

    answer = response.choices[0].message.content
    return try_extract_from_backticks(answer)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=DEFAULT_MODEL)
    parser.add_argument('--prefix-last', action='store_true', help='Add the messages from the last history entry before the command.')
    parser.add_argument('command', nargs='?', help='Optional command (will be read from stdin if not provided)')
    args = parser.parse_args()

    if args.command is None:
        command = input().strip()
    else:
        command = args.command.strip()

    history = []
    if args.prefix_last:
        with open(DEFAULT_LOG_FILE, 'r') as file:
            last_entry = json.loads(file.readlines()[-1])
            history.extend([msg for msg in last_entry['payload']['messages'] if msg['role'] != 'system'])
            history.append(dict(role='assistant', content=last_entry['responses'][0]['message']['content']))

    try:
        response = main(command, history=history, model=args.model)
        print(response)

    except OpenAIError as e:
        print(f"An error occured: {e}", file=sys.stderr)

    except Exception as e:
        print(f"An unhandled error occured: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
