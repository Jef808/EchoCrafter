#!/usr/bin/env python3

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


def log(payload, response, log_file=DEFAULT_LOG_FILE):
    """Create a log entry for a single query / answer pair."""
    log_entry = {
        "timestamp": response['created'],
        "model": response['model'],
        "payload": payload,
        "responses": response['choices'],
        "usage": response['usage']
    }
    with open(log_file, 'a+') as f:
        f.write(json.dumps(log_entry) + '\n')


def make_payload(query, model):
    """Make the payload for the OpenAI API."""
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": query}
        ]
    }
    return payload


def main(query, *, model=DEFAULT_MODEL):
    """Send query to OpenAI's chat completion endpoint."""
    openai_client = OpenAI(api_key=get_api_key())
    payload = make_payload(query, model)

    response = openai_client.chat.completions.create(**payload)
    log(payload, response)

    return response.choices[0].message.content


def handle_user_input():
    """Gather user input."""
    user_input = input()
    return user_input.strip()


if __name__ == "__main__":
    import argparse
    import sys
    from openai import OpenAIError

    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=DEFAULT_MODEL)
    parser.add_argument('query', nargs='?', help='Optional query')
    args = parser.parse_args()

    query = ' '.join(map(lambda x: x.strip(), args.query))
    if query is None:
        query = handle_user_input()

    try:
        response = main(query, model=args.model)
        print(response)

    except OpenAIError as e:
        print(f"An error occured: {e}", file=sys.stderr)

    except Exception as e:
        print(f"An unhandled error occured: {e}", file=sys.stderr)
