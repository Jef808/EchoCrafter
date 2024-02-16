"""Declare the Config object's structure here."""

from __future__ import annotations

from os import PathLike
from dataclasses import dataclass
from typing import TypedDict

class Directories(TypedDict):
    """A simple namespace for the directories in the Config object."""

    project_root: PathLike
    data_dir: PathLike


class Files(TypedDict):
    """A simple namespace for the directories in the Config object."""

    cheetah_model_file: PathLike
    porcupine_laptop_keyword_file: PathLike
    rhino_context_file: PathLike
    transcript_begin_wav: PathLike
    transcript_success_wav: PathLike


class Sockets(TypedDict):
    """A simple namespace for the directories in the Config object."""

    socket_path: str


class ApiKeys(TypedDict):
    """A simple namespace for the API keys in the Config object."""

    openai_api_key: str
    picovoice_api_key: str


class MicrophoneSettings(TypedDict):
    """A simple namespace for the microphone settings in the Config object."""

    device_index: int
    sample_rate: int
    frame_length: int
    intent_collection_timeout_secs: float
    transcript_collection_timeout_secs: float


class EnvironmentVariables(TypedDict):
    """Use these to manually trigger the wakeword and/or set the intent and slots."""

    wakeword: str
    intent: str
    slots: str


@dataclass(frozen=True, kw_only=True)
class Config:
    """A simple namespace for the Config object."""

    paths=TypedDict('paths', {
        'directories': Directories,
        'files': Files,
        'sockets': Sockets
    })
    apiKeys: ApiKeys
    microphoneSettings: MicrophoneSettings
    environmentVariables: EnvironmentVariables


def setup_config(*args, **kwargs):
    """Return the Config object."""
    try:
        return Config(**kwargs)
    except ValueError as e:
        raise ValueError(f"Invalid configuration: {e}") from e
