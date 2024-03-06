PYTHON_BASE_PROMPT = [
    {
        "role": "system",
        "content": "Your task is to perform the following five steps:\n"
                   "1. **Analysis**: Carefully analyze the intent and requirements for the script described in the user message\n"
                   "2. **Code**: In a `## CODE:` section, provide a python script which will fulfill the user's request\n"
                   "3. **Comments**: Carefully annotate all functions and the script with docstrings according to common practice\n"
                   "4. **Types**: From the user's description, infer the expected input and output types and add type hints to all function signatures\n"
                   "5. **Metadata**: Review the user intent along with your response and include a FILENAME for saving the script to a file.\n"
                                    "Also provide a DESCRIPTION containing a summary of functionalities of the generated script.\n"
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

CONTINUATION_PROMPT = [
    {
        "role": "system",
        "content": "Carefully review the initial user intent and requirements along with the assistant's response.\n"
                   "In the second user message, they can be asking for clarification, additional information, adding more requirements or asking you to revise the assistant's response.\n"
                   "You should address the user's request and provide the necessary information\n"
                   "If the user is asking for changes, determine if it is new requirements or if the previous assistant's response does not fully meet the original requirements.\n"
                   "In the latter case, treat the task as an 'edit' task and formulate the changes as a `git diff` patch to be applied to the original code.\n"
                   "In any case, respect the original assistant's formatting and structure by providing similar **CODE**, **FILENAME** and **DESCRIPTION** sections."
    }
]

SHELL_BASE_PROMPT = [
    {
        "role": "system",
        "content": "1. **Analysis**: Carefully analyze the intent of the provided command\n"
                   "2. **Code**: Generate a zsh shell script which, when executed on a linux system, will run that command "
                   "3. **Comments**: Carefully annotate all functions and the script itself with docstrings according to common practice "
                   "4. **Types**: From the provided command, infer the expected input and output types and add type hints to the function signature "
                   "5. **Metadata**: Provide a FILENAME for saving the script to a file and a DESCRIPTION reflecting the user's prompt for retrieving the script."
    },
    {
        "role": "system", "name": "example_user",
        "content": "```\nGive me the absolute path to my home directory\n```"
    },
    {
        "role": "system", "name": "example_assistant",
        "content": '## CODE:\n```zsh\n# print the content of the $HOME environment variable to standard output.\necho $HOME\n```\n\n## FILENAME:\nprint_home_dir.sh\n\n## DESCRIPTION:\nA script to print the home directory of the current user.'
    }
]
