#!/usr/bin/env python3

import argparse
import subprocess
import re
from typing import Optional


WINDOW_NAMES_ALIAS = {
    "browser": "chrome",
    "chrome": "chrome",
    "emacs": "emacs",
    "fire_fox": "firefox",
    "google_search": "chrome",
    "internet": "chrome",
    "kitty": "kitty",
    "shell": "kitty",
    "sound": "pavucontrol",
    "sound_control": "pavucontrol",
    "web": "chrome",
}


def focus_window_by_name(window_name: str):
    """Focus the window with the given name."""
    name = WINDOW_NAMES_ALIAS.get(window_name, '')
    subprocess.Popen(
        ['xdotool', 'search', '--onlyvisible', '--class', name, 'windowactivate']
    )


def focus_window_by_number(window_number: str):
    """Focus the window with the given number."""
    m = re.match(r'\d+', window_number)
    if m is not None:
        number = m.group(0)
        subprocess.Popen(['stumpish', 'select-window-by-number', number])


def main():
    parser = argparse.ArgumentParser(description='Focus a window by its name or number.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--window-number', type=str, help='Window number to focus.')
    group.add_argument('--window_name', type=str, help='Window name to focus.')

    args = parser.parse_args()

    # Call the focus_window function with the parsed arguments
    if args.window_number:
        focus_window_by_number(window_number=args.window_number)
    elif args.window_name:
        name = WINDOW_NAMES_ALIAS.get(args.window_name, '')
        if name:
            focus_window_by_name(window_name=name)


if __name__ == '__main__':
    main()
