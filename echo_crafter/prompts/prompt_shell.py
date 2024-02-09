#!/home/jfa/projects/echo-crafter/.venv/bin/python

import re
import json
import os
from pathlib import Path
from openai import OpenAI


DEFAULT_MODEL = "gpt-4"
DEFAULT_LOG_FILE = Path(os.getenv("XDG_DATA_HOME")) / "openai/logs.jsonl"


def get_api_key():
    """Get the OpenAI API key from the password store."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        import subprocess
        api_key = subprocess.check_output(["pass", "openai.com/api_key"])
        api_key = str(api_key, encoding="utf-8").rstrip()
    return api_key


def make_payload(prompt, model):
    """Make the payload for the OpenAI API."""
    system_prompt = ("carefully analyze the intent of the provided command "
                     "then replace it with a zsh shell script which, when executed on a linux system, will run that command")
    example = [{"role": "system", "name": "example_user", "content": "```\ngive me the absolute path to my home directory\n```"},
               {"role": "system", "name": "example_assistant", "content": "```zsh\necho $HOME\n```"}]
    payload = {
        "model": model,
        "stop": "\n```",
        "messages": [
            {"role": "system", "content": system_prompt}
        ]
    }
    payload['messages'].extend(example)
    payload['messages'].append({"role": "user", "content": f"```\n{prompt.strip()}\n```"})
    return payload


def format_response(content):
    """Extract the response from the content."""
    matches = re.search(r"```([\s\S]*?)```", content)
    if matches:
        return matches.group(1)
    return content


def log(payload, response, log_file=DEFAULT_LOG_FILE):
    """Log the payload and response to a file."""
    log_entry = {
        "language": "shell",
        "timestamp": response.created,
        "model": response.model,
        "payload": payload,
        "responses": response.choices,
        "usage": response.usage
    }
    with open(log_file, 'a+') as f:
        f.write(json.dumps(log_entry) + '\n')


def main(command, *, model=DEFAULT_MODEL):
    """
    Ask OpenAI's `model` to generate a shell script according to `command`.

    Returns OpenAI's full response object.
    """
    openai_client = OpenAI(api_key=get_api_key())
    payload = make_payload(command, model)

    response = openai_client.chat.completions.create(**payload)
    log(payload, response)

    return format_response(response.choices[0].message.content)


def handle_user_input():
    """Gather user input."""
    user_input = input()
    return user_input.strip()


if __name__ == '__main__':
    import argparse
    import sys
    from openai import OpenAIError

    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=DEFAULT_MODEL)
    parser.add_argument('command', nargs='?', help='Optional command')
    args = parser.parse_args()

    command = ' '.join(args.command)
    if command is None:
        command = handle_user_input()

    try:
        response = main(command, model=args.model)
        print(response)

    except OpenAIError as e:
        print(f"An error occured: {e}", file=sys.stderr)

    except Exception as e:
        print(f"An unhandled error occured: {e}", file=sys.stderr)
