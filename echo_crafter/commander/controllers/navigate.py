#!/usr/bin/env python3

"""Open a project, directory or website given."""

import subprocess
from typing import Optional
from utils import current_active_window, project_directory
from echo_crafter.commander import dictionary as cmd_dict


def navigate_website(website_name: str) -> None:
    """Open the given website in the given browser."""

    active_window_name = current_active_window()

    browser_name = ("google-chrome-stable" if "chrome" in active_window_name else
                    "firefox" if "firefox" in active_window_name else
                    "chromium" if "chromium" in active_window_name else
                    None)

    if browser_name is not None:
        print(f"Navigating to {website_name} in {browser_name}")
        url = cmd_dict.slots_dictionary["websiteName"].get(website_name)
        with subprocess.Popen([browser_name, url]):
            pass
    else:
        print("No browser found in the active window")


def navigate_directory_shell(directory_name: str) -> None:
    """Change the current directory to DIRECTORY_NAME.

    This function is intended to be used when the active window
    is that of a shell.
    """

    content_string = f"cd {directory_name}"
    with subprocess.Popen(["xdotool",
                           "type",
                           "--clearmodifiers",
                           "--delay",
                           "0",
                           content_string]) as proc:
        proc.wait()
    with subprocess.Popen(["xdotool",
                           "key",
                           "KP_Enter"]):
        print(f"Changed directory to {directory_name}")


def navigate_directory_emacs(directory_name: str) -> None:
    """Evaluate the Emacs function 'find-file-other-window'.

    Typically, the buffer of the other window will be a 'dired'
    buffer at DIRECTORY_NAME, or the content of the file in case
    DIRECTORY_NAME is not a directory.
    """

    emacs_socket = "/run/user/1000/emacs/server"
    with subprocess.Popen(["emacsclient",
                           "-s",
                           emacs_socket,
                           "-e",
                           f'(find-file-other-window "{directory_name}")']):
        print(f"Opening {directory_name} in Emacs")


def navigate_directory(directory_name: str) -> None:
    """Open the given directory."""

    print(f"Navigating to {directory_name}")

    active_window_name = current_active_window()

    if "Emacs" in active_window_name:
        print(f'Running emacsclient -e (find-file-other-window "{directory_name}")')
        navigate_directory_emacs(directory_name)

    elif "kitty" in active_window_name:
        content = f"cd {directory_name}"
        print(f"Running 'xdotool type --clearmodifers --delay 0 {content} && xdotool key KP_Enter'")
        with subprocess.Popen(["xdotool",
                               "type",
                               "--clearmodifiers",
                               "--delay",
                               "0",
                               content]) as proc:
            proc.wait()
        with subprocess.Popen(["xdotool",
                               "key",
                               "KP_Enter"]):
            pass


def main(*,
         directory_name: Optional[str] = None,
         project_name: Optional[str] = None,
         website_name: Optional[str] = None) -> None:
    """Open the given project in the given directory."""

    print(f"Executing `navigate` intent with locals {locals()}")

    directory_name = (directory_name if directory_name
                      else project_directory(project_name) if project_name
                      else None)

    if directory_name:
        print(f"Directory name: {directory_name}")
        navigate_directory(directory_name)

    elif project_name:
        print(f"Project name: {project_name}")
        directory_name = project_directory(project_name)
        navigate_directory(directory_name)

    elif website_name:
        print(f"Website name: {website_name}")
        navigate_website(website_name)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Script description')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--directory_name', help='Directory name')
    group.add_argument('--project_name', help='Project name')
    group.add_argument('--website_name', help='Website name')
    args = parser.parse_args()

    main(directory_name=args.directory_name,
         project_name=args.project_name,
         website_name=args.website_name)
