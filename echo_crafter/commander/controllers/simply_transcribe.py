#!/usr/bin/env python3

import time
import subprocess
from typing import Callable, Optional
from threading import Thread
from pvrecorder import PvRecorder
from pvcheetah import create, CheetahError
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger

logger = setup_logger(__name__)

def _execute(callback_partial: Optional[Callable[..., None]] = None, callback_final: Optional[Callable[..., None]] = None, timeout_seconds=6.0):
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""

    try:
        cheetah = create(
            access_key=Config['PICOVOICE_API_KEY'],
            endpoint_duration_sec=Config['ENDPOINT_DURATION_SEC'],
            model_path=Config['CHEETAH_MODEL_FILE']
        )
        try:
            recorder = PvRecorder(frame_length=512)
            recorder.start()
            start_time = time.time()
            partial_transcripts = []

            try:
                while recorder.is_recording:
                    partial_transcript, is_endpoint = cheetah.process(recorder.read())
                    partial_transcripts.append(partial_transcript)
                    if callback_partial is not None:
                        callback_partial(partial_transcript)
                    if is_endpoint or time.time() - start_time > timeout_seconds:
                        partial_transcript = cheetah.flush()
                        partial_transcripts.append(partial_transcript)
                        if callback_partial is not None:
                            callback_partial(partial_transcript)
                        if callback_final is not None:
                            callback_final(''.join(partial_transcripts))
                        break
            finally:
                recorder.stop()

        except CheetahError as e:
            logger.error("Failed transcribing audio with pvCheetah: ", e)

    finally:
        cheetah.delete()


def execute(*, callback_partial: Optional[Callable[..., None]] = None, callback_final: Optional[Callable[..., None]] = None):
    if callback_partial is None and callback_final is None:
        callback_partial = send_to_keyboard
        callback_final = send_to_clipboard
    Thread(target=_execute, args=(callback_partial, callback_final,)).start()


def send_to_keyboard(content: str) -> None:
    """Send the content to the keyboard."""
    subprocess.Popen(['xdotool', 'type', '--clearmodifiers', '--delay', '0', content])


def send_to_clipboard(content: str) -> None:
    """Send the content to the clipboard."""
    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
    process.communicate(input=content.encode('utf-8'))
