#!/usr/bin/env python3

import time
import subprocess
from typing import Callable
from threading import Thread
from pvrecorder import PvRecorder
from pvcheetah import create, CheetahError
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger

logger = setup_logger(__name__)

def _execute(callback: Callable[..., None], *, timeout_seconds=12):
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

            try:
                while True:
                    partial_transcript, is_endpoint = cheetah.process(recorder.read())
                    callback(partial_transcript)
                    if is_endpoint or time.time() - start_time > timeout_seconds:
                        callback(cheetah.flush())
                        break
            finally:
                recorder.stop()

        except CheetahError as e:
            logger.error("Failed transcribing audio with pvCheetah: ", e)

    finally:
        cheetah.delete()


def execute(*, slots):
    if slots.get('destination') is not None:
        destination = slots['destination']
        if destination in ['clipboard', 'keyboard']:
            callback = get_callback(destination)
        else:
            raise ValueError(f"Invalid destination slot value: {destination}.")
    else:
        callback = lambda x: send_to_keyboard(x) and send_to_clipboard(x)

    Thread(target=_execute, args=(callback,)).start()


def get_callback(destination: str) -> Callable[..., None]:
    match destination:
        case 'clipboard':
            return send_to_clipboard
        case 'keyboard':
            return send_to_keyboard
        case _:
            raise ValueError(f"Invalid destination slot value: {destination}.")


def send_to_keyboard(content: str) -> None:
    """Send the content to the keyboard."""
    subprocess.Popen(['xdotool', 'type', '--clearmodifiers', '--delay', '0', content])


def send_to_clipboard(content: str) -> None:
    """Send the content to the clipboard."""
    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
    process.communicate(input=content.encode('utf-8'))
