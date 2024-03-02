PYTHON_BASE_PROMPT = [
    {
        "role": "system",
        "content": "1. **Analysis**: Carefully analyze the intent of the provided command\n"
                   "2. **Code**: Generate a python script which, when executed after installing the necessary packages, will run that command "
                   "3. **Comments**: Carefully annotate all functions and the script itself with docstrings according to common practice "
                   "4. **Types**: From the provided command, infer the expected input and output types and add type hints to the function signature "
                   "5. **Metadata**: Provide a FILENAME for saving the script to a file and a DESCRIPTION reflecting the user's prompt for retrieving the script."
    },
    {
        "role": "system", "name": "example_user",
        "content": "Take a string as input and, if it exists, focus the window having a class matching the string."
    },
    {
        "role": "system", "name": "example_assistant",
        "content": '## CODE:\n```python\nimport subprocess\nimport sys\n\ndef focus_x_window(class_name: str) -> None:\n  """Switch window focus by class name."""\n  subprocess.Popen(["xdotool", "search", "--onlyvisible", "--class", class_name, "windowactivate"])\n```\n\n## FILENAME:\nfocus_window.py\n\n## DESCRIPTION:\nA function to focus active X11 windows by class name.'
    }
]

SHELL_BASE_PROMPT = [
    {
        "role": "system",
        "content": "carefully analyze the intent of the provided command then replace it with a zsh shell script which, when executed on a linux system, will run that command"
    },
    {
        "role": "system", "name": "example_user",
        "content": "```\ngive me the absolute path to my home directory\n```"
    },
    {
        "role": "system", "name": "example_assistant",
        "content": "```zsh\necho $HOME\n```"
    }
]

ELISP_BASE_PROMPT = [
    {
        "role": "system",
        "content": "carefully analyze the intent of the provided command then replace it with an emacs-lisp s-expression which, when evaluated in a doom-emacs environment, will run that command"
    },
    {
        "role": "system", "name": "example_user",
        "content": "```\nopen the file at the current cursor position\n```"

    },
    {
        "role": "system", "name": "example_assistant",
        "content": "```el\n(find-file (thing-at-point 'filename))\n```"
    }
]
