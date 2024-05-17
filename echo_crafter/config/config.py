"""@file Configuration for the echo-crafter package."""

from subprocess import check_output
from pathlib import Path
from typing import Literal, List, Optional, TypedDict


def get_project_root() -> Path:
    """Get the root of the project."""
    return Path(__file__).resolve().parent.parent.parent


def password_store_get(provider: str, key: str) -> str:
    """Get a password from the password store."""
    return str(check_output(["pass", f"echo_crafter/{provider}_{key}"]), encoding="utf-8").strip()


def build_path(rel_path: str) -> str:
    """Build an absolute path from the given path relative to root."""
    path = get_project_root() / rel_path
    return str(path.resolve().absolute())


class _Config(TypedDict):
    """Configuration for the echo-crafter package."""

    PROJECT_ROOT: str
    DATA_DIR: str
    CONTROLLERS_DIR: str

    PICOVOICE_API_KEY: str
    DEEPGRAM_API_KEY: str

    FRAME_RATE: int
    FRAME_LENGTH: int
    CHANNELS: int
    BUFFER_SIZE: int
    ENDPOINT_DURATION_SEC: float

    PORCUPINE_KEYWORD_FILE: str
    PORCUPINE_MODEL_FILE_EN: str
    PORCUPINE_MODEL_FILE_FR: str
    CHEETAH_MODEL_FILE: str
    LEOPARD_MODEL_FILE: str
    RHINO_CONTEXT_FILE: str
    RHINO_CONTEXT_SPEC: str

    DEEPGRAM_MODEL: str
    DEEPGRAM_LANGUAGE: Optional[str]
    DEEPGRAM_SMART_FORMAT: Optional[bool]
    DEEPGRAM_FEATURES: Optional[List[Literal['sentiment', 'summarize', 'topics', 'intents']]]
    DEEPGRAM_CUSTOM_TOPIC: Optional[List[str]]
    DEEPGRAM_CUSTOM_INTENT: Optional[List[str]]

    WAKE_WORD_DETECTED_WAV: str
    INTENT_SUCCESS_WAV: str


Config: _Config = {
    "PROJECT_ROOT":            str(get_project_root()),
    "DATA_DIR":                build_path("data"),
    "CONTROLLERS_DIR":         build_path("echo_crafter/commander/controllers"),

    "PICOVOICE_API_KEY":       password_store_get('picovoice', 'api_key'),
    "DEEPGRAM_API_KEY":        password_store_get('deepgram', 'api_key'),

    "FRAME_RATE":              16000,
    "FRAME_LENGTH":            512,
    "BUFFER_SIZE":             512 * 2 * 15,  # 15 seconds
    "ENDPOINT_DURATION_SEC":   1.5,

    "PORCUPINE_KEYWORD_FILE":  build_path("data/Pierrette_fr_linux_v3_0_0.ppn"),
    "PORCUPINE_MODEL_FILE_EN": build_path("data/porcupine_params_en.pv"),
    "PORCUPINE_MODEL_FILE_FR": build_path("data/porcupine_params_fr.pv"),
    "CHEETAH_MODEL_FILE":      build_path("data/speech-command-cheetah.pv"),
    "LEOPARD_MODEL_FILE":      build_path("data/speech-command-leopard.pv"),
    "RHINO_CONTEXT_FILE":      build_path("data/computer-commands_en_linux.rhn"),
    "RHINO_CONTEXT_SPEC":      build_path("data/computer-commands.yml"),

    "DEEPGRAM_MODEL":          "nova-2-conversationalai",
    "DEEPGRAM_LANGUAGE":       "en-US",
    "DEEPGRAM_SMART_FORMAT":   None,
    "DEEPGRAM_FEATURES":       ['summarize', 'topics', 'intents'],
    "DEEPGRAM_CUSTOM_TOPIC":   None,
    "DEEPGRAM_CUSTOM_INTENT":  None,

    "WAKE_WORD_DETECTED_WAV":  build_path("data/transcript_begin.wav"),
    "INTENT_SUCCESS_WAV":      build_path("data/transcript_success.wav"),
}
