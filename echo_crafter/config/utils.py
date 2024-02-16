#!/usr/bin/env python3

"""Utility functions for generating the Config object."""

from os import environ
from pathlib import Path

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).resolve().parent


def get_default_data_dir() -> Path:
    """Return the default data directory for the project."""
    return get_project_root() / "data"


def get_socket_dir() -> Path:
    """Return the default socket directory for the project."""
    return Path(environ.get('XDG_RUNTIME_DIR', '~/.local/share')) / 'transcription'


def generate_path_for_pv_files():
    """Return the path to the corresponding binary file."""
    DATA_DIR = get_default_data_dir()
    return dict(
        cheetah = DATA_DIR / "speech-command-cheetah-v1.pv",
        porcupine = DATA_DIR / "laptop_en_linux_v3_0_0.ppn",
        rhino = DATA_DIR / "computer-commands_en_linux_v3_0_0.rhn"
    )

def get_openai_api_key():
    """Get the OpenAI API key from the password store."""
    from os import getenv
    from subprocess import check_output

    api_key = getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = check_output(["pass", "openai.com/api_key"], text=True)
    return api_key

def get_picovoice_api_key():
    """Get the Picovoice API key from the password store."""
    from os import getenv
    from subprocess import check_output

    api_key = getenv("PICOVOICE_API_KEY")
    if not api_key:
        api_key = check_output(["pass", "picovoice.com/api_key"], text=True)
    return api_key
