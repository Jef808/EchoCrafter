import json
import sys
from openai import OpenAI

prompt = input()

openai_client = OpenAI()

# openai api call
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "The user messages are generated from an assemblyAI real-time transcript."
                                      "Using emacs and doom-emacs functions with lsp and magit, respond with an emacs-lisp s-expression which when evaluated will execute the command in the transcript."
                                      "Assuming I am in a projectile project, avoid hard-coded filepaths or entity names by incorporating fuzzy search in your script."},
        {"role": "user", "content": prompt}
    ]
}

print("Sending transcript to openai...", file=sys.stderr)
response = openai_client.chat.completions.create(**payload)

py_response = response.model_dump()

print(json.dumps(py_response, indent=2), file=sys.stderr)

content = py_response['choices'][0]['message']['content']

print(content)
