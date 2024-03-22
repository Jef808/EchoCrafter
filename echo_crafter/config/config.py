"""@file Configuration for the echo-crafter package."""

import os
from dataclasses import dataclass
from subprocess import check_output
from pathlib import Path
from typing import TypedDict


def get_project_root() -> Path:
    """Get the root of the project."""
    return Path(__file__).resolve().parent.parent.parent


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
    COMMANDS_DIR: str
    PYTHON_PACKAGES: str

    PICOVOICE_API_KEY: str
    PORCUPINE_KEYWORD_FILE: str
    CHEETAH_MODEL_FILE: str
    LEOPARD_MODEL_FILE: str
    RHINO_CONTEXT_FILE: str
    RHINO_CONTEXT_SPEC: str
    FRAME_LENGTH: int
    BUFFER_SIZE: int
    ENDPOINT_DURATION_SEC: float

    WAKE_WORD_DETECTED_WAV: str
    INTENT_SUCCESS_WAV: str


Config: _Config = {
    "PROJECT_ROOT":           str(get_project_root()),
    "DATA_DIR":               build_path("data"),
    "COMMANDS_DIR":           build_path("echo_crafter/commander/controllers"),
    "PYTHON_PACKAGES":        build_path(".venv/lib/python3.11/site-packages/python_packages"),

    "PICOVOICE_API_KEY":      str(os.getenv('PICOVOICE_API_KEY')),
    "PORCUPINE_KEYWORD_FILE": build_path("data/echo-crafter_linux.ppn"),
    "CHEETAH_MODEL_FILE":     build_path("data/speech-command-cheetah.pv"),
    "LEOPARD_MODEL_FILE":     build_path("data/speech-command-leopard.pv"),
    "RHINO_CONTEXT_FILE":     build_path("data/computer-commands_en_linux.rhn"),
    "RHINO_CONTEXT_SPEC":     build_path("data/computer-commands.yml"),
    "FRAME_LENGTH":           512,
    "BUFFER_SIZE":            512 * 2 * 30,  # 30 seconds
    "ENDPOINT_DURATION_SEC":  1.5,

    "WAKE_WORD_DETECTED_WAV": build_path("data/transcript_begin.wav"),
    "INTENT_SUCCESS_WAV":     build_path("data/transcript_success.wav"),
}
