#!/home/jfa/projects/echo-crafter/.venv/bin/python

import argparse
import json
import subprocess
from pathlib import Path
import os
from openai import OpenAI
from rich.console import Console

console = Console()

client = None

GPT_MODEL = "gpt-4"
DEFAULT_LOG_FILE = Path(os.getenv("XDG_DATA_HOME")) / "openai/logs.jsonl"

chat_log = []
usage = {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}


def get_api_key():
    """Get the OpenAI API key from the password store."""
    api_key = subprocess.check_output(["pass", "openai.com/api_key"])
    api_key = str(api_key, encoding="utf-8").rstrip()
    return api_key


def handle_user_input():
    """Gather user input."""
    user_input = input()
    return user_input.strip()


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


def ChatGPT(query, temperature):
    """Make a call to OpenAI's chat completions endpoint."""
    user_query = [
        {"role": "user", "content": query}
    ]
    send_query = (chat_log + user_query)
    payload = {
        "model": GPT_MODEL,
        "messages": send_query,
        "temperature": temperature
    }
    response = client.chat.completions.create(**payload)
    answer = response.choices[0].message.content
    log(payload, response)
    chat_log.append({"role": "assistant", "content": answer})
    return answer


def main():
    """Run the main chat loop."""
    global client
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=GPT_MODEL)
    parser.add_argument('--temperature', type=float, help='Temperature to use when querying the model.', default=1.0)
    parser.add_argument('command', nargs='?', help='Optional command')
    args = parser.parse_args()

    client = OpenAI(api_key=get_api_key())

    query = None

    if args.command:
        query = ' '.join(args.command)

    while True:
        try:
            if query is not None:
                console.print(query, style="cyan")
            else:
                console.print("User query (Q/q[uit] to quit)...", style="bold cyan")
                query = handle_user_input()
            if query.lower() == 'q' or query.lower() == 'quit':
                console.print("User terminated chat", style="bold red")
                break

            with console.status("[bold yellow]Waiting for ChatGPT's answer..."):
                answer = ChatGPT(query, args.temperature)
                query = None

            console.print(answer, style="green")

        except KeyboardInterrupt:
            console.print("User terminated chat", style="bold red")
            break


if __name__ == '__main__':
    main()
