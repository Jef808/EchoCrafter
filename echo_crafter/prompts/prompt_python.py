#!/usr/bin/env python3

import argparse
import time
import json
import sys
import re
from openai import OpenAI
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
try:
    from echo_crafter.config import OpenAIConfig
except ImportError:
    sys.path.append('os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))')
    from echo_crafter.config import OpenAIConfig
from echo_crafter.prompts.utils import estimate_token_count
from echo_crafter.config import OpenAIConfig


def prompt_template():
    """Insert the user query in the prompt template."""
    system_message = {
        "role": "system",
        "content": "1. carefully analyze the intent of the provided command "
                   "2. respond with a python script which, when executed after installing the necessary packages, will run that command "
                   "3. Carefully annotate all functions and the script itself with docstrings that accurately reflect intent of the user prompt and describes the code you generated."
    }
    example_message = [
        {"role": "system", "name": "example_user", "content": "Take a string as input and, if it exists, focus the window having a class matching the string."},
        {"role": "system", "name": "example_assistant", "content": '''```python\nimport subprocess\nimport sys\n\ndef focus_x_window(class_name: str) -> None:\n  """Switch window focus by class name."""\n  subprocess.Popen(["xdotool", "search", "--onlyvisible", "--class", class_name, "windowactivate"])\n```'''}
    ]
    return [system_message, *example_message]


class OpenAIAPI:
    """OpenAI API client."""

    def __init__(self):
        """Initialize the OpenAI API client."""
        self.client = OpenAI(api_key=OpenAIConfig['API_KEY'])
        self.messages = prompt_template()
        self.temperature = 0.4
        self.max_new_tokens = None
        self.messages_token_count = estimate_token_count(self.messages)
        self.model = OpenAIConfig['DEFAULT_MODEL']
        self.created = time.time()
        self.usage = {'completion_tokens': 0, 'prompt_tokens': 0, 'total_tokens': 0}


    def create_chat_completion(self, message):
        """Create a chat completion."""
        oaimsg = {"role": "user", "content": message}
        self.messages.append(oaimsg)

        self.messages_token_count += estimate_token_count([oaimsg])

        max_tokens = (self.messages_token_count + self.max_new_tokens
            if self.max_new_tokens is not None else 0)

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": self.messages,
            "max_tokens": max_tokens
        }

        response = self.client.chat.completions.create(**payload)
        self.usage['completion_tokens'] += response.usage.completion_tokens
        self.usage['prompt_tokens'] += response.usage.prompt_tokens
        self.usage['total_tokens'] += response.usage.total_tokens
        self.messages_token_count += response.usage.completion_tokens

        self.messages.append({"role": "assistant", "content": response.choices[0].message.content or ""})

        return response

    def log_session(self):
        """Log the session chat to a file."""
        try:
            log_entry = {
                "language": "python",
                "timestamp": self.created,
                "model": self.model,
                "temperature": self.temperature,
                "messages": self.messages,
                "usage": self.usage,
                "error": None
            }
            with open(OpenAIConfig['LOG_FILE'], 'a+') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            print(f"Error occurred while logging session: {e}", file=sys.stderr)
            print("Current messages:", self.messages, file=sys.stderr)


def format_response(content):
    """Extract the code blocks from the content."""
    split = re.split(r"```(\S+)\s", content)
    code_blocks = []
    while len(split) > 3:
        language = split[1]
        code = split[2].strip()
        code_blocks.append(code)
        split = split[3:]

    return language, '\n\n'.join(code_blocks)


def get_prompt_template_token_count():
    """Estimate the number of tokens in the prompt."""
    prompt = prompt_template()
    return estimate_token_count(prompt)


def main():
    parser = argparse.ArgumentParser(description='Process some arguments.')
    parser.add_argument('--model',
                        type=str,
                        help='Model to use.',
                        default=OpenAIConfig['DEFAULT_MODEL'],
                        )
    parser.add_argument('--max_new_tokens',
                        type=int,
                        help='Specify an upper bound on number of tokens generated per response.',
                        )
    parser.add_argument('command',
                        nargs='?',
                        help='Optional command',
                        )
    args = parser.parse_args()

    console = Console()
    session = PromptSession(history=FileHistory(OpenAIConfig['HISTORY_FILE']))
    api = OpenAIAPI()

    command = args.command
    api.model = args.model
    api.max_new_tokens = args.max_new_tokens

    try:
        while True:
            if command is not None:
                console.print(">>> ", command, style="bold cyan")
            else:
                console.print("User command (Q/q[uit] to quit)...", style="bold cyan")
                command = session.prompt(">>> ")
                if command.lower() == 'q' or command.lower() == 'quit':
                    console.print("User terminated chat", style="bold red")
                    break

            with console.status("[bold yellow]Waiting for ChatGPT's answer..."):
                response = api.create_chat_completion(command)
                command = None

            content = response.choices[0].message.content
            console.print(content, style="green")

    except KeyboardInterrupt:
        console.print("User terminated chat", style="bold red")

    finally:
        api.log_session()

    return None

if __name__ == '__main__':
    main()
