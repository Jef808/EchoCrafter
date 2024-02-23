"""@file Configuration for the echo-crafter package."""

import os
from dataclasses import dataclass
from subprocess import check_output
from pathlib import Path
from typing import TypedDict


def get_project_root() -> Path:
    """Get the root of the project."""
    return Path(os.environ.get('EC_ROOT', '')) \
        or Path(__file__).parent.parent.parent


def get_picovoice_api_key() -> str:
    """Get the Picovoice API key from the environment."""
    api_key = os.environ.get('PICOVOICE_API_KEY')
    if not api_key:
        api_key = str(check_output(["pass", "cnsole.picovoice.com/api_key"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No Picovoice API key found.")
    return api_key


@dataclass(init=False, frozen=True)
class _Config(TypedDict):
    """Configuration for the echo-crafter package."""

    PROJECT_ROOT: str
    DATA_DIR: str
    PYTHON_PACKAGES_DIR: str

    PICOVOICE_API_KEY: str
    CHEETAH_MODEL_FILE: str
    FRAME_LENGTH: int
    ENDPOINT_DURATION_SEC: float

    TRANSCRIPT_BEGIN_WAV: str
    TRANSCRIPT_SUCCESS_WAV: str
    SOCKET_PATH: str


Config: _Config = {
    "PROJECT_ROOT":           str(get_project_root()),
    "DATA_DIR":               str(get_project_root()/"data"),
    "PYTHON_PACKAGES_DIR":    str(get_project_root()/".venv/lib/python3.11/site-packages/python_packages"),

    "PICOVOICE_API_KEY":      str(os.getenv('PICOVOICE_API_KEY')),
    "CHEETAH_MODEL_FILE":     str(get_project_root()/"data/speech-command-cheetah-v2.pv"),
    "FRAME_LENGTH":           512,
    "ENDPOINT_DURATION_SEC":  1.5,

    "TRANSCRIPT_BEGIN_WAV":   str(get_project_root()/"data/transcript_begin.wav"),
    "TRANSCRIPT_SUCCESS_WAV": str(get_project_root()/"data/transcript_success.wav"),
    "SOCKET_PATH":            str(Path(os.environ.get('EC_SOCKET_FILE', '/tmp/echo-crafter.sock')))
}
