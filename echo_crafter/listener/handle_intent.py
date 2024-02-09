#!/usr/bin/env python3

import contextlib
import importlib
import os
from pathlib import Path
import subprocess
import yaml

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT'))


def send_to_keyboard(content):
    """Send the content to the keyboard."""
    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', content]
    )


def set_volume(volume, percentage=None, volume_setting=None):
    """Set the volume to the given value."""
    if volume_setting is not None:
        mute = '0' if volume_setting == 'unmute' else '1'
        subprocess.Popen(
            ['pactl', 'set-sink-mute', '@DEFAULT_SINK@', mute]
        )
    elif percentage is not None:
        subprocess.Popen(
            ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{percentage}%']
        )
    else:
        raise ValueError('Either percentage or volume_setting must be provided')


def prompt_openai(transcript, *, language=None, ask_question=False):
    """Prompt openai using the script appropriate for the given language."""
    if ask_question:
        name = '.prompt_openai'
        package = 'echo_crafter.prompts'
    elif language == 'shell':
        name = '.prompt_shell'
        package = 'echo_crafter.prompts'
    elif language == 'emacs':
        name = '.prompt_elisp'
        package = 'echo_crafter.prompts'
    else:
        name = '.prompt_python'
        package = 'echo_crafter.prompts'

    module = importlib.import_module(name, package)
    try:
        response = module.main(transcript)
        return response
    except Exception as e:
        print(e)


def focus_window(*, window_number=None, window_name=None):
    """Focus the window with the given name."""
    import re

    if window_number is not None:
        m = re.match(r'\d+', window_number)
        if m is not None:
            try:
                number = int(m.group(0))
                subprocess.Popen(
                    ['stumpish', 'select-window-by-number', number]
                )
            except ValueError:
                pass
    elif window_name is not None:
        print(f"focusing window {window_name}")
        subprocess.Popen(
            ['xdotool', 'search', '--onlyvisible', '--class', window_name, 'windowactivate']
        )


def open_window(*, window_name):
    """Open a window with the given name."""
    if window_name in ['terminal', 'shell', 'kitty']:
        subprocess.Popen(
            ['stumpish', 'open-window', window_name]
        )
    subprocess.Popen(
        ['stumpish', 'open-window', window_name]
    )


class TranscriptHandler:
    """Handle speech transcripts according to a given intent."""

    class PartialTranscriptHandler:
        """Handle partial transcripts according to a given intent."""

        def __init__(self, intent_list):
            """Initialize a PartialTranscriptHandler instance."""


        def __enter__(self):
            """Enter the context manager."""
            pass

        def __exit__(self, exc_type, exc_value, traceback):
            """Exit the context manager."""
            pass

    class FinalTranscriptHandler:
        """Handle final transcripts according to a given intent."""

        def __init__(self, intent):
            """Initialize a FinalTranscriptHandler instance."""
            self.intent = intent

        def __enter__(self):
            """Enter the context manager."""
            pass

        def __exit__(self, exc_type, exc_value, traceback):
            """Exit the context manager."""
            pass

    def __init__(self, intent_config_file):
        """Initialize an IntentHandler instance."""
        with open(intent_config_file, 'r') as file:
            self.intent_config = yaml.safe_load(file)

    @contextlib.contextmanager
    def partial_transcript_handler(self, intent):
        """Handle a partial transcript according to the given intent."""
        pass

    @contextlib.contextmanager
    def final_transcript_handler(self, intent):
        """Handle a final transcript according to the given intent."""
        pass
