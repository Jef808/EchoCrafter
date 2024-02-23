"""@file Configuration for the prompt package."""

from dataclasses import dataclass
import os
from subprocess import check_output
from pathlib import Path
from typing import TypedDict


def get_openai_api_key() -> str:
    """Get the OpenAI API key from the password store."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key is None:
        api_key = str(check_output(["pass", "openai.com/api_key"]), encoding="utf-8").rstrip()
    if not api_key:
        raise ValueError("No OpenAI API key found.")
    return api_key


def get_openai_log_path() -> str:
    """Get the path to the OpenAI log file."""
    xdg_data_dir = Path(os.getenv("XDG_DATA_HOME") or Path.home()/".local/share")
    return str(xdg_data_dir/"openai/logs.jsonl")


@dataclass
class _OpenAIConfig(TypedDict):
    """Configuration for the prompt package."""

    API_KEY: str
    LOG_FILE: str
    DEFAULT_MODEL: str


OpenAIConfig: _OpenAIConfig = {
    "API_KEY": get_openai_api_key(),
    "LOG_FILE": get_openai_log_path(),
    "DEFAULT_MODEL": "gpt-4"
}
