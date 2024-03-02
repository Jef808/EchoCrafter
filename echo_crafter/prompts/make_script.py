#!/usr/bin/env python3

import argparse
import sys
import re
sys.path.append('os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))')
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from echo_crafter.config import OpenAIConfig
from echo_crafter.prompts import OpenAIAPI
from echo_crafter.prompts.templates import (
    PYTHON_BASE_PROMPT,
    SHELL_BASE_PROMPT,
    ELISP_BASE_PROMPT
)


def extract_sections_from_markdown(markdown_text: str, sections: list[str]) -> dict:
     """
     Extracts specific sections from a markdown document.

     Args:
         - markdown_text (str): The markdown text to be parsed.
         - sections (list[str]): A list of section names to be extracted.

     Returns:
         dict: A dictionary containing the extracted content as {'section': content}.
     """
     # Regular expressions for extracting the sections
     section_patterns = [f"## {section}:\n(.*)\n\n## {sections[i+1]}" for i, section in enumerate(sections[:-1])]
     section_patterns.append(f"## {sections[-1]}:\n(.*)")
     # Extracting the content
     section_contents = [re.search(section_pattern, markdown_text, re.DOTALL) for section_pattern in section_patterns]

     # Preparing the result dictionary
     result = {
         section: (section_contents[i].group(1).strip() if section_contents[i] is not None else "") for i, section in enumerate(sections)  # type: ignore
     }

     return result


def extract_code_block(content):
    """Parse the answer content."""
    match = re.search(r"```(?:\S+)(.*)```", content, re.DOTALL)
    if match is not None:
        return match.group(1).strip()


def main():
    parser = argparse.ArgumentParser(description='Process some arguments.')

    parser.add_argument('command',          nargs='?',  help='Optional command')
    parser.add_argument('--model',          type=str,   help='Model to use.', default=OpenAIConfig['DEFAULT_MODEL'])
    parser.add_argument('--language',       type=str,   help='Language to use.', default='python')
    parser.add_argument('--temperature',    type=float, help='Sampling temperature to use [floating point number between 0 and 2]', default=0.2)
    parser.add_argument('--max_new_tokens', type=int,   help='Specify an upper bound on number of tokens generated per response.')

    args = parser.parse_args()

    match args.language:
        case 'python':
            base_prompt = PYTHON_BASE_PROMPT
            extension = ".py"
            shebang = "#!/usr/bin/env python3\n\n"
        case 'shell':
            shebang = "#!/usr/bin/env zsh\n\n"
            extension = ".sh"
            base_prompt = SHELL_BASE_PROMPT
        case 'elisp':
            shebang = "#!/usr/bin/env emacs --script\n\n"
            extension = ".el"
            base_prompt = ELISP_BASE_PROMPT
        case _:
            raise ValueError(f"Unsupported language: {args.language}")

    console = Console()
    session = PromptSession(history=FileHistory(OpenAIConfig['HISTORY_FILE']))
    api = OpenAIAPI(base_prompt, model=args.model, max_new_tokens=args.max_new_tokens, temperature=args.temperature)

    command = args.command

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

            sections = extract_sections_from_markdown(response, ["CODE", "FILENAME", "DESCRIPTION"])
            console.print("Code Section:", Markdown(sections["CODE"]))
            console.print("Filename Section:", sections["FILENAME"])
            console.print("Description Section:", sections["DESCRIPTION"])

            _fname = sections["FILENAME"]
            fname = _fname if _fname and _fname.endswith(extension) else None

            if fname is not None:
                console.print(f"Save to {sections['FILENAME']}? [Y/n]", style="bold cyan")
                save = prompt("> ")
                if save.lower() == 'y':
                    try:
                        code = extract_code_block(sections["CODE"])
                        with open(_fname, 'w') as f:
                            f.write(f"{shebang}{code}")
                            console.print(f"Saved to {_fname}", style="bold green")
                            break
                    except OSError as e:
                        console.print(f"Error saving to {_fname}: {e}", style="bold orange")
                else:
                    console.print("Let me know how I can edit my previous answer to better reflect your intent.", style="bold green")

    except KeyboardInterrupt:
        console.print("User terminated chat", style="bold red")

    finally:
        if api.usage['total_tokens'] > 0:
            api.log_session()

    return None

if __name__ == '__main__':
    main()
