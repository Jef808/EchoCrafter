#!/usr/bin/env python3

import re
from typing import List
from echo_crafter.commander.dictionary import slots_dictionary

def format_intent(intent: str) -> str:
    """Format the intent string to be used as a key."""
    return camel_to_snake(intent)


def format_slots(slots: dict) -> dict:
    """Convert the slots dictionary to command-line arguments."""
    return {camel_to_snake(k): camel_to_snake(v) for k, v in slots.items()}


def translate_slots(slots: dict) -> dict:
    """Translate the slots to the corresponding values in the dictionary."""
    return {k: slots_dictionary.get(k, {}).get(v, v) for k, v in slots.items()}


def camel_to_snake(camel_str: str, delimiter: str = '_') -> str:
    """
    Convert a string from CamelCase to snake_case.

    Args:
    camel_str (str): The CamelCase string to be converted.
    delimiter (str): The character to use as the delimiter in the snake_case string.

    Returns:
    str: The converted snake_case string.
    """
    # Insert an underscore before any uppercase letter followed by a lowercase letter, then lowercase the entire string
    camel_str.replace('\s', delimiter)
    snake_str = re.sub(r'(?<!^)(?=[A-Z][a-z])', delimiter, camel_str).lower()
    return snake_str
