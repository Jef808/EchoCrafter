from echo_crafter.listener.utils import (
    socket_connection,
    Microphone
)
from echo_crafter.logger import setup_logger
from echo_crafter.config import Config

import subprocess
import traceback


def play_sound(wav_file):
    """Play a ding sound to indicate that the wake word was detected."""
    subprocess.Popen(["aplay", "-q", str(wav_file)])


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    logger = setup_logger()

    with Microphone() as mic:
        try:
            while True:
                mic.wait_for_wake_word()
                play_sound(Config['TRANSCRIPT_BEGIN_WAV'])

                with socket_connection(Config['SOCKET_PATH']) as client:
                    mic.process_and_transmit_utterance(client)
                    play_sound(Config['TRANSCRIPT_SUCCESS_WAV'])

        except KeyboardInterrupt:
            pass

        except Exception as e:
            logger.error(f"An error occured:\n{e}")
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
