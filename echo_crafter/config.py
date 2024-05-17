import subprocess
from typing import NamedTuple
from pydantic_settings import BaseSettings, SettingsConfigDict

"""Configuration for the echo-crafter package."""


class PicovoiceConfig(BaseSettings):
    """Settings for the audio input."""

    frame_length: int
    buffer_size: int
    endpoint_duration_sec: float

    porcupine_keyword_file: str
    porcupine_model_file: str
    cheetah_model_file: str
    leopard_model_file: str
    rhino_context_file: str
    rhino_context_spec: str

    deepgram_api_key: str

class ControllersConfig(BaseSettings):
    """Settings for the controllers."""

    dir: str
    emacs_socket: str
    shells: list[str]
    browsers: list[str]

class _Config(BaseSettings):
    """Settings for the echo-crafter package."""

    PROJECT_ROOT: str
    DATA_DIR: str
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
    INTENT_FAILURE_WAV: str

    pv: PicovoiceConfig
    controllers: ControllersConfig

    class Config:
        """Settings for the config."""

        env_prefix = "ECHO_CRAFTER_"


def gnupass(entry: str) -> str:
    return subprocess.check_output(['pass', entry], text=True).strip()



Config = _Config()
