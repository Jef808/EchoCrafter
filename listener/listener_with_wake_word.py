#!/usr/bin/env python3

from contextlib import contextmanager
import os
from pathlib import Path
import pvcheetah
import pvporcupine
import pvrecorder
import socket
import sys

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT'))
CHEETAH_MODEL_FILE = PROJECT_ROOT / "listener/data/speech-command-cheetah-v1.pv"
PORCUPINE_MODEL_FILE = PROJECT_ROOT / "listener/data/laptop_en_linux_v3_0_0.ppn"
TRANSCRIPT_BEGIN_WAV = PROJECT_ROOT / "listener/data/transcript_begin.wav"
TRANSCRIPT_SUCCESS_WAV = PROJECT_ROOT / "listener/data/transcript_success.wav"

SOCKET_PATH = "/tmp/transcript_socket"


@contextmanager
def porcupine_context_manager(keywords, sensitivities):
    """Create a Porcupine instance and yield it. Delete the instance upon exit."""
    porcupine_instance = None
    try:
        porcupine_instance = pvporcupine.create(
            keywords=keywords,
            sensitivities=sensitivities,
            access_key=os.getenv('PICOVOICE_API_KEY'),
            model_path=PORCUPINE_MODEL_FILE
        )
        yield porcupine_instance
    finally:
        if porcupine_instance:
            porcupine_instance.delete()


@contextmanager
def cheetah_context_manager():
    """Create a Cheetah instance and yield it. Delete the instance upon exit."""
    cheetah_instance = None
    try:
        cheetah_instance = pvcheetah.create(access_key=os.getenv('PICOVOICE_API_KEY'),
                                            endpoint_duration_sec=1.3,
                                            model_path=str(CHEETAH_MODEL_FILE))
        yield cheetah_instance
    finally:
        if cheetah_instance:
            cheetah_instance.delete()


@contextmanager
def recorder_context_manager(device_index, frame_length):
    """Create a PvRecorder instance and yield it. Delete the instance upon exit."""
    recorder_instance = None
    try:
        recorder_instance = pvrecorder.PvRecorder(
            device_index=device_index,
            frame_length=frame_length
        )
        recorder_instance.start()
        yield recorder_instance
    finally:
        if recorder_instance:
            recorder_instance.stop()
            recorder_instance.delete()


def play_sound(wav_file):
    """Play a ding sound to indicate that the wake word was detected."""
    os.system(f"aplay {wav_file}")


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    keywords = ["computer", "laptop"]
    sensitivities = [0.1]
    device_index = -1
    frame_length = 512

    def console_status(flag):
        return 'Listening for wake word' if not flag else 'Transcribing'

    client = None

    try:
        with porcupine_context_manager(keywords, sensitivities) as porcupine, \
             cheetah_context_manager() as cheetah, \
             recorder_context_manager(device_index, frame_length) as recorder:

            wake_word_detected = False
            is_endpoint = False

            while True:
                pcm_frame = recorder.read()

                if not wake_word_detected:
                    keyword_index = porcupine.process(pcm_frame)
                    if keyword_index >= 0:
                        wake_word_detected = True
                        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        client.connect(SOCKET_PATH)
                        play_sound(TRANSCRIPT_BEGIN_WAV)

                else:
                    partial_transcript, is_endpoint = cheetah.process(pcm_frame)
                    client.sendall((partial_transcript).encode())
                    if is_endpoint:
                        partial_transcript = cheetah.flush()
                        client.sendall((partial_transcript + 'STOP').encode())
                        client.close()
                        client = None
                        wake_word_detected = False
                        play_sound(TRANSCRIPT_SUCCESS_WAV)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occured: {e}", file=sys.stderr)
    finally:
        if client is not None:
            client.sendall('STOP'.encode())
            client.close()


if __name__ == '__main__':
    main()
