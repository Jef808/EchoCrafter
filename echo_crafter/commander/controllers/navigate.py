#!/usr/bin/env python3

"""Open a project, directory or website given."""

import subprocess
from typing import Optional
from utils import current_active_window

def navigate_browser(website_name: str, browser_name: str) -> None:
    """Open the given website in the given browser."""

    print(f"Navigating to {website_name} in {browser_name}")

    subprocess.Popen([browser_name,
                      website_name])

def navigate_directory_shell(directory_name: str) -> None:
    """Change the current directory to DIRECTORY_NAME.

    This function is intended to be used when the active window
    is that of a shell.
    """

    content_string = f"cd {directory_name}"
    subprocess.run(["xdotool",
                    "type",
                    "--clearmodifiers",
                    "--delay",
                    "0",
                    content])
    subprocess.Popen(["xdotool",
                      "key",
                      "KP_Enter"])

def navigate_directory_emacs(directory_name: str) -> None:
    """Evaluate the Emacs function 'find-file-other-window'.

    Typically, the buffer of the other window will be a 'dired'
    buffer at DIRECTORY_NAME, or the content of the file in case
    DIRECTORY_NAME is not a directory.
    """

    emacs_socket = "/run/user/1000/emacs/server"
    print(f'Running emacsclient -e (find-file-other-window "{directory_name}")')
    subprocess.Popen(["emacsclient",
                      "-e",
                      f'(find-file-other-window "{directory_name}")'])

def navigate_directory(directory_name: str) -> None:
    """Open the given directory."""

    print(f"Navigating to {directory_name}")

    active_window_name = current_active_window()

    if "Emacs" in active_window_name:
        print(f'Running emacsclient -e (find-file-other-window "{directory_name}")')
        subprocess.Popen(["emacsclient",
                          "-e",
                          f'(find-file-other-window "{directory_name}")'])
    elif "kitty" in active_window_name:
        content = f"cd {directory_name}"
        print(f"Running 'xdotool type --clearmodifers --delay 0 {content} && xdotool key KP_Enter'")
        subprocess.run(["xdotool",
                        "type",
                        "--clearmodifiers",
                        "--delay",
                        "0",
                        content])
        subprocess.Popen(["xdotool",
                          "key",
                          "KP_Enter"])


def main(*,
         directory_name: Optional[str] = None,
         project_name: Optional[str] = None,
         website_name: Optional[str] = None) -> None:
    """Open the given project in the given directory."""

    print(f"Executing `navigate` intent with locals {locals()}")

    active_window_name = subprocess.check_output(
        ["xdotool", "getactivewindow", "getwindowclassname"]
    ).decode("utf-8")

    print(f"Active window class name: {active_window_name}")

    directory_name = (directory_name if directory_name else
                      f"~/projects/{project_name}" if project_name else
                      None)

    if directory_name:
        print(f"Directory name: {directory_name}")
        if "Emacs" in active_window_name:
            print(f'Running emacsclient -e (find-file-other-window "{directory_name}")')
            subprocess.Popen(["emacsclient",
                              "-e",
                              f'(find-file-other-window "{directory_name}")'])
        elif "kitty" in active_window_name:
            content = f"cd {directory_name}"
            print(f"Running 'xdotool type --clearmodifers --delay 0 {content} && xdotool key KP_Enter'")
            subprocess.run(["xdotool",
                            "type",
                            "--clearmodifiers",
                            "--delay",
                            "0",
                            content])
            subprocess.Popen(["xdotool",
                              "key",
                              "KP_Enter"])

    elif website_name:
        print(f"Website name: {website_name}")
        browser_name = ("google-chrome-stable" if "chrome" in active_window_name else
                        "firefox" if "firefox" in active_window_name else
                        "chromium" if "chromium" in active_window_name else
                        None)
        if browser_name:
            subprocess.Popen([browser_name,
                              website_name])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Script description')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--directory_name', help='Directory name')
    group.add_argument('--project_name', help='Project name')
    group.add_argument('--website_name', help='Website name')
    args = parser.parse_args()

    arg = None

    if args.directory_name:
        arg = args.directory_name
    elif args.project_name:
        arg = args.project_name
    elif args.website_name:
        arg = args.website_name

    if arg is None:
        raise ArgumentError("One of --directory_name, --project_name or --website_name must be provided")

    main(arg)
