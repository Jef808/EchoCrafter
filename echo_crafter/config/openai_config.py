"""@file Configuration for the prompt package."""

from dataclasses import dataclass
import os
from subprocess import check_output
from pathlib import Path
from typing import Literal, TypedDict


def get_openai_api_key() -> str:
    """Get the OpenAI API key from the password store."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key is None:
        api_key = str(check_output(["pass", "openai/echo-crafter"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No OpenAI API key found.")
    return api_key

def get_openai_log_path() -> str:
    """Get the path to the OpenAI log file."""
    xdg_data_dir = Path(os.getenv("XDG_DATA_HOME") or Path.home()/".local/share")
    return str(xdg_data_dir/"openai/new_logs.jsonl")

def get_history_file() -> str:
    """Get the path to the OpenAI history file."""
    xdg_data_dir = Path(os.getenv("XDG_DATA_HOME") or Path.home()/".local/share")
    return str(xdg_data_dir/"openai/history.jsonl")


@dataclass
class Pricing(TypedDict):
    """Pricing information for a model.

    The pricing information is given in units of USD/(1 million tokens).
    """

    input: float
    output: float


@dataclass
class Model(TypedDict):
    """A model object."""

    name: Literal[
        "gpt-4-0125-preview",
        "gpt-3.5-turbo-0125",
        "text-embedding-3-small",
        "text-embedding-3-large"
    ]
    pricing: Pricing


@dataclass
class _OpenAIConfig(TypedDict):
    """Configuration for the prompt package."""

    API_KEY: str
    LOG_FILE: str
    HISTORY_FILE: str
    DEFAULT_MODEL: str
    MODELS: list[Model]


OpenAIConfig: _OpenAIConfig = {
    "API_KEY": get_openai_api_key(),
    "LOG_FILE": get_openai_log_path(),
    "HISTORY_FILE": get_history_file(),
    "MODELS": [
        {
            "name": "gpt-4-0125-preview",
            "pricing": {"input": 10, "output": 30}
        },
        {
            "name": "gpt-3.5-turbo-0125",
            "pricing": {"input": 0.5, "output": 1.5}
        },
        {
            "name": "text-embedding-3-small",
            "pricing": {"input": 0.02, "output": 0.02}
        },
        {
            "name": "text-embedding-3-large",
            "pricing": {"input": 0.13, "output": 0.13}
        }
    ],
    "DEFAULT_MODEL": "gpt-4-0125-preview"
}
