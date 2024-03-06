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
