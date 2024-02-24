"""Listen for a wake word and transcribe speech until endpoint is detected."""

import subprocess
import traceback
import socket
from contextlib import contextmanager
from echo_crafter.listener.utils import (
    microphone
)
from echo_crafter.logger import setup_logger
from echo_crafter.config import Config

def play_sound(wav_file):
    """Play a ding sound to indicate that the wake word was detected."""
    subprocess.Popen(["aplay", "-q", wav_file])


def wake_word_callback():
    """Play a ding sound to indicate that the wake word was detected."""
    play_sound(Config['TRANSCRIPT_BEGIN_WAV'])


@contextmanager
def create_transcription_callback():
    """Connect to the transcription socket and send it all partial transcripts."""

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(Config['SOCKET_PATH'])

        def callback(partial_transcript):
            """Send the partial transcript to the active window."""
            client.sendall((partial_transcript).encode())

        yield callback

    finally:
        client.close()


def transcription_success_callback():
    """Play a ding sound to indicate that the final transcript was received."""
    play_sound(Config['TRANSCRIPT_SUCCESS_WAV'])


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    logger = setup_logger()

    with microphone() as mic:
        try:
            while True:
                with create_transcription_callback() as transcription_callback:
                    mic.wait_for_wake_word(wake_word_callback)

                    mic.process_and_transmit_utterance(transcription_callback, transcription_success_callback)

        except KeyboardInterrupt:
            pass

        except Exception as e:
            logger.error("An error occured %s", e)
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
