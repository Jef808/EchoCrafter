#!/home/jfa/projects/echo-crafter/.venv/bin/python

import json
import subprocess
from pathlib import Path
import os
from openai import OpenAI
import sys

GPT_MODEL = "gpt-4"
DEFAULT_LOG_FILE = Path(os.getenv("XDG_DATA_HOME")) / "openai/logs.jsonl"

chat_log = []


def get_api_key():
    """Get the OpenAI API key from the password store."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
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


def ChatGPT(client, query, temperature):
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
    log(payload, response)

    return response


def handle_user_input():
    """Gather user input."""
    query = input()
    return query.strip()


def main(query, *, model=GPT_MODEL, should_chat=True):
    """Run the main chat loop."""
    openai_client = OpenAI(api_key=get_api_key())

    response = ChatGPT(openai_client, query, 1.0)
    answer = response.choices[0].message.content

    while should_chat:
        chat_log.extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer}
        ])

        query = handle_user_input()

        with console.status("[bold yellow]Waiting for ChatGPT's answer..."):
            answer = ChatGPT(query, args.temperature)
            query = None

            console.print(answer, style="green")


if __name__ == '__main__':
    import argparse
    from rich.console import Console
    console = Console()

    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model', type=str, help='Model to use.', default=GPT_MODEL)
    parser.add_argument('--temperature', type=float, help='Temperature to use when querying the model.', default=1.0)
    parser.add_argument('--chat', action='store_true', help='Start a chat session.')
    parser.add_argument('query', nargs='?', help='Optional command')
    args = parser.parse_args()

    query = None

    if not args.query:
        console.print("Enter query (Q/q[uit] to quit)...", style="bold cyan")
        query = handle_user_input()

        if query.lower() == 'q' or query.lower() == 'quit':
            console.print("User terminated chat", style="bold red")
            sys.exit(0)
    else:
        query = ' '.join(map(lambda x: x.strip, args.query))

    should_chat = args.chat
