#!/usr/bin/env python

import argparse
import subprocess
import json
import sys
from openai import OpenAI


DEFAULT_MODEL = "gpt-4-1106-preview" # "gpt-4"
DEFAULT_TEMPERATURE = 0.2

parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--from-speech', type=bool, help='Indicate if input is a voice transcript.')
parser.add_argument('--script-language', type=str, help='Language that should be used for generating the script. One of SHELL, ELISP or PYTHON', required=True)
parser.add_argument('--model', type=str, help='Model to use.', default=DEFAULT_MODEL)
parser.add_argument('--temperature', type=float, help='Temperature value.', default=DEFAULT_TEMPERATURE)
parser.add_argument('--custom_instructions', type=str, help='Additional instructions for the system prompt.')


def make_system_prompt(args):
    system_prompt = "From assemblyAI transcripts expressing a command," if 'from_speech' in args else ""

    match args['script_language']:
        case 'ELISP':
            system_prompt += "Emacs s-expression, without explanations, executable in a Doom Emacs environment with lsp, projectile and magit"
        case 'SHELL':
            system_prompt += "shell script, without explanations, executable in a typical Linux environment"
        case 'PYTHON':
            system_prompt += "python script, without explanations, executable by Python3 with numpy, requests and other standard libraries"
        case _:
            system_prompt += f"script in the {script_language} language, intended to be executed in a typical environment"
            print(f"WARNING: language {script_language} has only generic version of the prompt", file=sys.stderr)

    system_prompt += "to execute the command. Utilize fuzzy search for filepaths and names instead of hardcoded placeholders."
    system_prompt += f" {args['custom_instructions']}" if 'custom_instructions' in args else ""

    return system_prompt


def make_payload(args, prompt):
    return {
        "model": args['model'],
        "message": [
            {"role": "system", "content": make_system_prompt(args)},
            {"role": "user", "content": prompt}
        ],
        "temperature": args['temperature']
    }

def get_api_key():
    p_api_key = subprocess.run(["pass", "openai.com/api_key"], capture_output=True)
    if not p_api_key.stdout:
        print("ERROR: Failed to retrieve openai.com/api_key pass entry", file=sys.stderr)
        sys.exit(3)
    return str(p_api_key.stdout, encoding="utf-8").strip()


if __name__ == '__main__':
    openai_client = OpenAI(api_key=get_api_key())

    args = parser.parse_args()

    prompt = input()

    payload = make_payload(args, prompt)

    print(f"Built the body of the prompt as {json.dumps(payload, indent=2)}", file=sys.stderr)

    response = openai_client.chat.completions.create(**payload)
    py_response = response.model_dump()

    print(f"Response: {json.dumps(py_response, indent=2)}", file=sys.stderr)

    content = py_response['choices'][0]['message']['content']

    print(content)
