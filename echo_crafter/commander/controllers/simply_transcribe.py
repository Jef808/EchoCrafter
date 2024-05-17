#!/usr/bin/env python3

import time
import subprocess
from typing import Callable, Optional
from threading import Thread
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from echo_crafter.speech_processor.resources import (
    create_cheetah,
    create_recorder,
)

logger = setup_logger(__name__)


def run(callback_partial: Optional[Callable[..., None]] = None,
        callback_final: Optional[Callable[..., None]] = None,
        timeout_seconds=6.0):
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""

    with create_cheetah(model_file=Config['CHEETAH_MODEL_FILE']) as transcriber, \
         create_recorder() as recorder:
        recorder.start()
        start_time = time.time()
        partial_transcripts = []
        while recorder.is_recording:
            partial_transcript, is_endpoint = transcriber.process(recorder.read())
            partial_transcripts.append(partial_transcript)
            if callback_partial is not None:
                callback_partial(partial_transcript)
                if is_endpoint or time.time() - start_time > timeout_seconds:
                    partial_transcript = transcriber.flush()
                    partial_transcripts.append(partial_transcript)
                    if callback_partial is not None:
                        callback_partial(partial_transcript)
                    if callback_final is not None:
                        callback_final(''.join(partial_transcripts))
                    break


def main():
    """Run the speech processor in a separate thread."""
    callback_partial = send_to_keyboard
    callback_final = send_to_clipboard
    Thread(target=run, args=(callback_partial, callback_final,)).start()
    #run(callback_partial, callback_final).start()


def send_to_keyboard(content: str) -> None:
    """Send the content to the keyboard."""
    with subprocess.Popen([
        'xdotool',
        'type',
        '--clearmodifiers',
        '--delay',
        '0',
        content
    ]) as proc:
        proc.communicate()


def send_to_clipboard(content: str) -> None:
    """Send the content to the clipboard."""
    with subprocess.Popen([
        'xclip',
        '-selection',
        'clipboard'
    ], stdin=subprocess.PIPE) as proc:
        proc.communicate(input=content.encode('utf-8'))


if __name__ == '__main__':
    main()
