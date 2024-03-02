"""Listen for a wake word and transcribe speech until endpoint is detected."""

import json
import subprocess
import traceback
from typing import List

#from .handle_intent import IntentHandler
from echo_crafter.logger import setup_logger
from echo_crafter.config import Config
from echo_crafter.types import Intent
from echo_crafter.listener.utils import microphone

logger = setup_logger(__name__)

def play_sound(wav_file) -> None:
    """Play a ding sound to indicate that the wake word was detected."""
    subprocess.Popen(['aplay', wav_file])


def on_wake_word_detected() -> None:
    """Play a ding sound to indicate that the wake word was detected."""
    play_sound(Config['TRANSCRIPT_BEGIN_WAV'])

def send_to_keyboard(content):
    """Send the content to the keyboard."""
    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', content]
    )


def on_intent_inferred(intent_obj: Intent) -> None:
    """Log the inferred intent and slots."""
    logger.info("Intent inferred: %s", json.dumps(intent_obj))
    #IntentHandler()
    print(json.dumps(intent_obj, indent=2))
    play_sound(Config['TRANSCRIPT_SUCCESS_WAV'])


partial_transcripts: List[str] = []


def on_partial_transcript(partial_transcript: str) -> None:
    """Send the partial transcript to the active window."""
    partial_transcripts.append(partial_transcript)
    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', partial_transcript]
    )


def on_final_transcript() -> None:
    """Log the accumulated partial transcripts"""
    final_transcript = ''.join(partial_transcripts)
    partial_transcripts.clear()
    logger.info("Final transcript: %s", final_transcript)


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    logger = setup_logger(__name__)

    with microphone() as mic:
        try:
            while True:
                mic.wait_for_wake_word(on_wake_word_detected)
                mic.infer_intent(on_intent_inferred)
                #mic.process_and_transmit_utterance(on_partial_transcript, on_final_transcript)

        except KeyboardInterrupt:
            mic.set_is_recording(False)

        except Exception as e:
            logger.error("An error occured %s", e)
            logger.error(traceback.format_exc())

        finally:
            mic.set_is_recording(False)

if __name__ == '__main__':
    main()
