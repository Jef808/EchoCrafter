import json
import sys
from openai import OpenAI

prompt = input()

openai_client = OpenAI()

# openai api call
payload = {
    "model": "gpt-4-1106-preview",
    "messages": [
        {"role": "system": "content": "Process AssemblyAI transcripts to extract Emacs commands. Respond with an Emacs Lisp s-expression that executes these commands in a Doom Emacs setup with lsp and magit. Ensure compatibility with Projectile, using fuzzy search to handle filepaths and names without hard-coding."},
        {"role": "user", "content": prompt}
    ]
}

print("Sending transcript to openai...", file=sys.stderr)
response = openai_client.chat.completions.create(**payload)

py_response = response.model_dump()

print(json.dumps(py_response, indent=2), file=sys.stderr)

content = py_response['choices'][0]['message']['content']

print(content)
