#!/usr/bin/env python3

import re

def camel_to_snake(camel_str: str) -> str:
    """
    Convert a string from CamelCase to snake_case.
    
    Args:
    camel_str (str): The CamelCase string to be converted.
    
    Returns:
    str: The converted snake_case string.
    """
    # Insert an underscore before any uppercase letter followed by a lowercase letter, then lowercase the entire string
    snake_str = re.sub(r'(?<!^)(?=[A-Z][a-z])', '_', camel_str).lower()
    return snake_str