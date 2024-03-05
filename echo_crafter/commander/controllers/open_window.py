import subprocess

WINDOW_NAMES = [
    "browser",
    "chrome",
    "emacs",
    "fire fox",
    "google search",
    "kitty",
    "shell",
    "sound",
    "sound control",
    "web",
]

WINDOW_NAMES_ALIAS = {
    "browser": "Google-chrome",
    "chrome": "Google-chrome",
    "emacs": "Emacs",
    "fire fox": "Firefox",
    "google search": "Google-chrome",
    "kitty": "kitty",
    "shell": "kitty",
    "sound": "pavucontrol",
    "sound control": "pavucontrol",
    "web": "Google-chrome",
}


def execute(*, slots):
    """Open a window with the given name."""
    if slots.get('window_name') is not None:
        window_name = slots['window_name']
        if window_name in WINDOW_NAMES_ALIAS:
            window_alias = WINDOW_NAMES_ALIAS[window_name]
        else:
            raise ValueError(f"Invalid window name: {window_name}.")
        ...

        # subprocess.Popen(
        #     ['stumpish', 'open-window', window_name]
        # )
