#!/usr/bin/env python3

from echo_crafter.config import Config

import os
import sys


def EnvOverride():
    """Monitor the environment for changes and update the relevant globals accordingly."""
    last_should_wait_for_keyword_s = ''
    last_intent_s = ''
    last_slots_s = ''
    should_wait_for_keyword = True
    preset_intent = None

    def check_for_env_settings():
        nonlocal last_should_wait_for_keyword_s
        nonlocal last_intent_s
        nonlocal last_slots_s
        nonlocal should_wait_for_keyword
        nonlocal preset_intent

        _should_wait_for_keyword_s = os.getenv(Config.environmentVariables.wakeword) or ''
        _intent_s = os.getenv(Config.environmentVariables.intent) or ''
        _slots_s = os.getenv(Config.environmentVariables.slots) or ''

        if _should_wait_for_keyword_s != last_should_wait_for_keyword_s:
            last_should_wait_for_keyword_s = _should_wait_for_keyword_s
            should_wait_for_keyword = _should_wait_for_keyword_s.lower() == 'false'

        if _intent_s != last_intent_s or _slots_s != last_slots_s:
            last_intent_s = _intent_s
            last_slots_s = _slots_s if _intent_s else ''

            intent = [True, _intent_s, {}] if _intent_s else None
            if _slots_s:
                slots_kv_s = _slots_s.split(',')
                try:
                    intent[2] = {k: v for k, v in (e.split('=') for e in slots_kv_s)}
                except ValueError:
                    print("ECHO_CRAFTER_INTENT_SLOTS should be a comma separated list of 'key=value' entries", file=sys.stderr)
                    intent = None
            preset_intent = intent

        return should_wait_for_keyword, preset_intent

    return check_for_env_settings
