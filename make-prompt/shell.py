#!/usr/bin/env python

import argparse
import subprocess
import json
import sys
from openai import OpenAI


DEFAULT_MODEL = "gpt-4-1106-preview"

parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--model', type=str,
                    help='Model to use.',
                    default=DEFAULT_MODEL)


def make_payload(args, prompt):
    system_prompt = ("You will be assigned a user command. Your mission is to generate a"
                     " zsh shell script that, when executed in an Arch Linux environment,"
                     " will run the command.\nDo not explain yourself or output anything else.")
    example = [{"role": "user", "content": "Command: Give me the absolute path to the home directory."},
               {"role": "assistant", "content": '```shell\necho $HOME\n```'}]
    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": system_prompt}
        ]
    }
    payload['messages'].extend(example)
    payload['messages'].append({"role": "user", "content": f"Command: {prompt}"})
    return payload


def get_api_key():
    p_api_key = subprocess.run(["pass", "openai.com/api_key"],
                               capture_output=True)
    if not p_api_key.stdout:
        print("ERROR: Failed to retrieve openai.com/api_key pass entry",
              file=sys.stderr)
        sys.exit(3)
    return str(p_api_key.stdout, encoding="utf-8").strip()


def format_response(content):
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


if __name__ == '__main__':
    openai_client = OpenAI(api_key=get_api_key())

    args = parser.parse_args()

    prompt = input()

    payload = make_payload(args, prompt)

    print(f"[PAYLOAD]: {json.dumps(payload, indent=2)}", file=sys.stderr)

    response = openai_client.chat.completions.create(**payload)
    py_response = response.model_dump()

    print(f"[RESPONSE]: {json.dumps(py_response, indent=2)}", file=sys.stderr)

    content = py_response['choices'][0]['message']['content']

    print(format_response(content))
