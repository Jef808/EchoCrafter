import re
import json
import subprocess
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


def execute(*, window_number: Optional[str] = None, window_name: Optional[str] = None):
    """Focus the window with the given name or number."""
    if window_number is not None:
        m = re.match(r'\d+', window_number)
        if m is not None:
            number = m.group(0)
            subprocess.Popen(['stumpish', 'select-window-by-number', number])
    elif window_name is not None:
        name = WINDOW_NAMES_ALIAS.get(window_name, '')
        subprocess.Popen(
            ['xdotool', 'search', '--onlyvisible', '--class', name, 'windowactivate']
        )
    else:
        raise ValueError(f"Invalid parameters for the 'focusWindow' intent")
