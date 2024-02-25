"""@file Configuration for the echo-crafter package."""

import os
from dataclasses import dataclass
from subprocess import check_output
from pathlib import Path
from typing import TypedDict


def get_project_root() -> Path:
    """Get the root of the project."""
    path = Path(os.environ.get('EC_ROOT', '')) \
        or Path(__file__).resolve().parent.parent.parent
    return path


def get_picovoice_api_key() -> str:
    """Get the Picovoice API key from the environment."""
    api_key = os.environ.get('PICOVOICE_API_KEY')
    if not api_key:
        api_key = str(check_output(["pass", "cnsole.picovoice.com/api_key"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No Picovoice API key found.")
    return api_key


def build_path(rel_path: str) -> str:
    """Build an absolute path from the given path relative to root."""
    return str(get_project_root() / rel_path)


@dataclass(init=False, frozen=True)
class _Config(TypedDict):
    """Configuration for the echo-crafter package."""

    PROJECT_ROOT: str
    DATA_DIR: str
    PYTHON_PACKAGES: str

    PICOVOICE_API_KEY: str
    CHEETAH_MODEL_FILE: str
    RHINO_CONTEXT_FILE: str
    FRAME_LENGTH: int
    ENDPOINT_DURATION_SEC: float

    TRANSCRIPT_BEGIN_WAV: str
    TRANSCRIPT_SUCCESS_WAV: str
    SOCKET_PATH: str


Config: _Config = {
    "PROJECT_ROOT":           str(get_project_root()),
    "DATA_DIR":               build_path("data"),
    "PYTHON_PACKAGES":        build_path(".venv/lib/python3.11/site-packages/python_packages"),

    "PICOVOICE_API_KEY":      str(os.getenv('PICOVOICE_API_KEY')),
    "CHEETAH_MODEL_FILE":     build_path("data/speech-command-cheetah-v2.pv"),
    "RHINO_CONTEXT_FILE":     build_path("data/computer-commands_en_linux_v3_0_0.rhn"),
    "FRAME_LENGTH":           512,
    "ENDPOINT_DURATION_SEC":  1.5,

    "TRANSCRIPT_BEGIN_WAV":   build_path("data/transcript_begin.wav"),
    "TRANSCRIPT_SUCCESS_WAV": build_path("data/transcript_success.wav"),
    "SOCKET_PATH":            str(Path(os.environ.get('EC_SOCKET_FILE', '/tmp/echo-crafter.sock')))
}
