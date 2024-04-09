#!/usr/bin/env python3

import subprocess
from typing import Optional

def execute(*, directory_name: Optional[str] = None, project_name: Optional[str] = None, website_name: Optional[str] = None) -> None:
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
