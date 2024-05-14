"""@file Configuration for the echo-crafter package."""

import os
from pydantic_settings import BaseSettings
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
        api_key = str(check_output(["pass", "echo_crafter/picovoice_api_key"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No Picovoice API key found.")
    else:
        os.environ['PICOVOICE_API_KEY'] = api_key
    return api_key


def get_deepgram_api_key() -> str:
    api_key = os.environ.get("DG_API_KEY")
    if not api_key:
        api_key = str(check_output(["pass", "echo_crafter/deepgram_api_key"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No Deepgram API key found.")
    else:
        os.environ['DEEPGRAM_API_KEY'] = api_key
    return api_key

def build_path(rel_path: str) -> str:
    """Build an absolute path from the given path relative to root."""
    return str(get_project_root() / rel_path)


class _Config(TypedDict):
    """Configuration for the echo-crafter package."""

    PROJECT_ROOT: str
    DATA_DIR: str
    CONTROLLERS_DIR: str

    PICOVOICE_API_KEY: str
    PORCUPINE_KEYWORD_FILE: str
    PORCUPINE_MODEL_FILE_EN: str
    PORCUPINE_MODEL_FILE_FR: str
    CHEETAH_MODEL_FILE: str
    LEOPARD_MODEL_FILE: str
    RHINO_CONTEXT_FILE: str
    RHINO_CONTEXT_SPEC: str
    FRAME_LENGTH: int
    BUFFER_SIZE: int
    ENDPOINT_DURATION_SEC: float

    PICOVOICE_API_KEY: str
    DEEPGRAM_API_KEY: str

    PORCUPINE_KEYWORD_FILE: str
    PORCUPINE_MODEL_FILE: str
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
    "PROJECT_ROOT":            str(get_project_root()),
    "DATA_DIR":                build_path("data"),
    "CONTROLLERS_DIR":         build_path("echo_crafter/commander/controllers"),

    "PICOVOICE_API_KEY":       get_picovoice_api_key(),
    "DEEPGRAM_API_KEY":        get_deepgram_api_key(),
    "PORCUPINE_KEYWORD_FILE":  build_path("data/Pierrette_fr_linux_v3_0_0.ppn"),
    "PORCUPINE_MODEL_FILE_EN": build_path("data/porcupine_params_en.pv"),
    "PORCUPINE_MODEL_FILE_FR": build_path("data/porcupine_params_fr.pv"),
    "CHEETAH_MODEL_FILE":      build_path("data/speech-command-cheetah.pv"),
    "LEOPARD_MODEL_FILE":      build_path("data/speech-command-leopard.pv"),
    "RHINO_CONTEXT_FILE":      build_path("data/computer-commands_en_linux.rhn"),
    "RHINO_CONTEXT_SPEC":      build_path("data/computer-commands.yml"),
    "FRAME_LENGTH":            512,
    "BUFFER_SIZE":             512 * 2 * 30,  # 30 seconds
    "ENDPOINT_DURATION_SEC":   2.5,

    "WAKE_WORD_DETECTED_WAV":  build_path("data/transcript_begin.wav"),
    "INTENT_SUCCESS_WAV":      build_path("data/transcript_success.wav"),
}
