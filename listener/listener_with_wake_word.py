#!/usr/bin/env python3

from contextlib import contextmanager
import os
from pathlib import Path
import pvcheetah
import pvporcupine
import pvrecorder
import socket
import subprocess
import sys

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT'))
CHEETAH_MODEL_FILE = PROJECT_ROOT / "listener/data/speech-command-cheetah-v1.pv"
PORCUPINE_LAPTOP_KEYWORD_FILE = PROJECT_ROOT / "listener/data/laptop_en_linux_v3_0_0.ppn"
TRANSCRIPT_BEGIN_WAV = PROJECT_ROOT / "listener/data/transcript_begin.wav"
TRANSCRIPT_SUCCESS_WAV = PROJECT_ROOT / "listener/data/transcript_success.wav"
SOCKET_PATH = Path(os.getenv('XDG_RUNTIME_DIR')) / "transcription"


@contextmanager
def porcupine_context_manager(keyword_paths, sensitivities):
    """Create a Porcupine instance and yield it. Delete the instance upon exit."""
    porcupine_instance = None
    try:
        porcupine_instance = pvporcupine.create(
            keyword_paths=keyword_paths,
            sensitivities=sensitivities,
            access_key=os.getenv('PICOVOICE_API_KEY')
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
        cheetah_instance = pvcheetah.create(
            access_key=os.getenv('PICOVOICE_API_KEY'),
            endpoint_duration_sec=1.3,
            model_path=str(CHEETAH_MODEL_FILE)
        )
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
    subprocess.Popen(["aplay", str(wav_file)])


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    keywords = ["computer"]
    keyword_paths = [PORCUPINE_LAPTOP_KEYWORD_FILE]
    keyword_paths.extend(pvporcupine.KEYWORD_PATHS[w] for w in keywords)
    keywords = [Path(w).stem.split('_')[0] for w in keyword_paths]
    sensitivities = [0.1] * len(keyword_paths)
    device_index = -1
    frame_length = 512
    client = None

    try:
        with porcupine_context_manager(keyword_paths, sensitivities) as porcupine, \
             cheetah_context_manager() as cheetah, \
             recorder_context_manager(device_index, frame_length) as recorder:

            wake_word_detected = False

            while True:
                pcm_frame = recorder.read()

                if not wake_word_detected:
                    keyword_index = porcupine.process(pcm_frame)
                    if keyword_index >= 0:
                        wake_word_detected = True
                        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        client.connect(str(SOCKET_PATH))
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
            client.sendall(b'STOP')
            client.close()


if __name__ == '__main__':
    main()
