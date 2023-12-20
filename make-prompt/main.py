import subprocess
import json
import sys
from openai import OpenAI

# model, temperature, system_prompt
import argparse

DEFAULT_MODEL = "gpt-4-1106-preview" # "gpt-4"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_SYSTEM_PROMPT = ("From assemblyAI transcripts expressing a command,"
                        "generate an Emacs s-expression, without explanations, executable in a Doom Emacs environment with lsp, projectile and magit which executes the command."
                        "Utilize fuzzy search for filepaths and names instead of hardcoded placeholders.")
                # "Generate an Emacs s-expression from assemblyAI transcripts command. Output only the executable expression, in Doom Emacs with lsp, projectile, and magit using fuzzy search"

parser = argparse.ArgumentParser(description='Process some arguments.')
parser.add_argument('--model', type=str, help='Model to use.', default="gpt-4-1106-preview")
parser.add_argument('--temperature', type=float, help='Temperature value.', default=0.2)
parser.add_argument('--system-prompt', type=str, help='System prompt to use.', default=DEFAULT_SYSTEM_PROMPT)

args = parser.parse_args()

def get_api_key():
    p_api_key = subprocess.run(["pass", "openai/api_key"], capture_output=True)
    if not p_api_key.stdout:
        print("ERROR: Failed to retrieve assemblyai.com/api_key pass entry", file=sys.stderr)
        sys.exit(3)
    return str(p_api_key.stdout, encoding="utf-8").strip()

openai_client = OpenAI(api_key=get_api_key())

prompt = input()

# openai api call
payload = {
    "model": args.model,
    "messages": [
        {"role": "system", "content": args.system_prompt},
        {"role": "user", "content": prompt}
    ],
    "temperature": args.temperature,
}

print("Sending transcript to openai...", file=sys.stderr)
response = openai_client.chat.completions.create(**payload)

py_response = response.model_dump()

print(json.dumps(py_response, indent=2), file=sys.stderr)

content = py_response['choices'][0]['message']['content']

print(content)
