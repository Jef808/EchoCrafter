import re
import json
import subprocess


WINDOW_NAMES_ALIAS = {
    "browser": "chrome",
    "chrome": "chrome",
    "emacs": "emacs",
    "fire fox": "firefox",
    "google search": "chrome",
    "internet": "chrome",
    "kitty": "kitty",
    "shell": "kitty",
    "sound": "pavucontrol",
    "sound control": "pavucontrol",
    "web": "chrome",
}


def execute(*, slots):
    """Focus the window with the given name."""
    if slots.get('windowNumber') is not None:
        window_number = slots['windowNumber']
        m = re.match(r'\d+', window_number)
        if m is not None:
            try:
                number = m.group(0)
                print(f"focusing window number {number}")
                subprocess.Popen(['stumpish', 'select-window-by-number', number])
            except ValueError:
                pass
    elif slots.get('windowName') is not None:
        window_name = slots['windowName']
        print(f"focusing window {window_name}")
        subprocess.Popen(
            ['xdotool', 'search', '--onlyvisible', '--class', window_name, 'windowactivate']
        )

    else:
        raise ValueError(f"Invalid slots for the 'focusWindow' intent:\n{json.dumps(slots)}")
