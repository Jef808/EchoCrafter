"""Configuration for the echo-crafter package."""

import os
from pathlib import Path
from typing import TypedDict

PROJECT_ROOT=Path(os.getenv('EC_ROOT') or '')
DATA_DIR=Path(os.getenv('EC_DATA_DIR') or '')

class _Config(TypedDict):
    CHEETAH_MODEL_FILE: str
    PICOVOICE_API_KEY: str
    FRAME_LENGTH: int
    ENDPOINT_DURATION_SEC: float
    TRANSCRIPT_BEGIN_WAV: str
    TRANSCRIPT_SUCCESS_WAV: str
    SOCKET_PATH: str


Config: _Config = {
    "CHEETAH_MODEL_FILE": str(DATA_DIR/"speech-command-cheetah-v1.pv"),
    "PICOVOICE_API_KEY": os.environ.get('PICOVOICE_API_KEY', ''),
    "FRAME_LENGTH": 512,
    "ENDPOINT_DURATION_SEC": 1.3,
    "TRANSCRIPT_BEGIN_WAV": str(DATA_DIR/"transcript_begin.wav"),
    "TRANSCRIPT_SUCCESS_WAV": str(DATA_DIR/"transcript_success.wav"),
    "SOCKET_PATH": str(Path(os.getenv('EC_SOCKET_FILE') or '/tmp/echo-crafter.sock'))
}

__all__ = ['Config']
