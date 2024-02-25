from enum import StrEnum
from typing import Any, NamedTuple, Tuple, List, Callable, TypeVar, Type

AudioFrame = List[int]

class IntentName(StrEnum):
    """Intent names for the voice commands."""

    UNKNOWN = "unknown"
    GET_SCRIPT = "getScript"
    ANSWER_QUESTION = "answerQuestion"
    TRANSCRIBE_TO_KEYBOARD = "simplyTranscribe"
    FOCUS_WINDOW = "focusWindow"
    OPEN_WINDOW = "openWindow"
    SET_VOLUME = "setVolume"
    CANCEL = "cancel"


class Slot(StrEnum):
    """Slot names for the intent's named parameters."""

    PROGRAMMING_LANGUAGE = "programmingLanguage"
    PROMPT_TYPE = "promptType"
    WINDOW_NAME = "windowName"
    VOLUME_SETTING = "volumeSetting"


class Intent(NamedTuple):
    """Named tuple for the intent."""

    intent: IntentName
    slots: List[Slot]


class MicrophoneCallbacks(NamedTuple):
    """Named tuple for the microphone callbacks."""

    on_wake_word: Callable[[], Any]
    on_intent: Callable[[Intent], Any]
    on_partial_transcript: Callable[[str], Any]
    on_final_transcript: Callable[[], Any]
