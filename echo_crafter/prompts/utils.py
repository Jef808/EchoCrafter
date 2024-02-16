#!/usr/bin/env python3

import re

pattern_between_backticks = re.compile(r"```(?:[^\n]+\n)?([\s\S]*?)```")


def try_extract_from_backticks(text):
    """
    Extract content contained in triple backticks.

    This allows for an arbitrary language name to be specified after the first
    triple backtick. The content is then extracted until the next one.

    If no triple backticks are found, the original text is returned.
    """
    matches = pattern_between_backticks.search(text)
    if matches:
        return matches.group(1)
    return text
