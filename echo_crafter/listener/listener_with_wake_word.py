from echo_crafter.config import Config
from .env_override import EnvOverride

from contextlib import contextmanager
import os
import json
from pathlib import Path
import pvcheetah
import pvporcupine
import pvrecorder
import pvrhino
import socket
import subprocess
import sys
import time


# Load the configuration
CONFIG = Config()


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
def rhino_context_manager(sensitivity):
    """
    Create a Rhino instance and yield it. Delete the instance upon exit.

    The Rhino context file is a file that contains the speech commands that Rhino should listen for.

    Args: sensitivity: float: The sensitivity of the wake word.
    """
    rhino_instance = None
    try:
        rhino_instance = pvrhino.create(
            access_key=os.getenv('PICOVOICE_API_KEY'),
            context_path=str(CONFIG.paths.files.rhino_context_file),
            sensitivity=sensitivity,
            endpoint_duration_sec=1.,
            require_endpoint=True
        )
        yield rhino_instance
    finally:
        if rhino_instance:
            rhino_instance.delete()

@contextmanager
def cheetah_context_manager():
    """Create a Cheetah instance and yield it. Delete the instance upon exit."""
    cheetah_instance = None
    try:
        cheetah_instance = pvcheetah.create(
            access_key=os.getenv('PICOVOICE_API_KEY'),
            endpoint_duration_sec=1.,
            model_path=str(CONFIG.paths.files.cheetah_model_file)
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
    subprocess.Popen(["aplay", "-q", str(wav_file)])


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    global should_continue

    keywords = ["computer"]
    keyword_paths = [CONFIG.paths.files.porcupine_laptop_keyword_file]
    keyword_paths.extend(pvporcupine.KEYWORD_PATHS[w] for w in keywords)
    keywords = [Path(w).stem.split('_')[0] for w in keyword_paths]
    sensitivity = 0.1
    sensitivities = [sensitivity] * len(keyword_paths)
    device_index = -1
    frame_length = 512
    client = None

    check_for_env_settings = EnvOverride()

    wake_word_detected = False
    intent = None
    step_timer = None

    def end_transcript(reason):
        """End the transcript and reset the state."""
        nonlocal wake_word_detected
        nonlocal intent
        nonlocal step_timer
        nonlocal client

        wake_word_detected = False
        intent = None
        step_timer = None
        client.sendall(f"<{reason}>".encode())
        client.close()
        client = None

    def send_intent(intent):
        """Send the intent to the keyboard."""
        nonlocal client
        intent_dict = {'intent': intent[1], 'slots': intent[2]}
        client.sendall(f"<RHINO_BEGIN>{json.dumps(intent_dict)}<RHINO_END>".encode())

    try:
        with porcupine_context_manager(keyword_paths, sensitivities) as porcupine, \
             rhino_context_manager(sensitivity) as rhino, \
             cheetah_context_manager() as cheetah, \
             recorder_context_manager(device_index, frame_length) as recorder:

            should_wait_for_keyword, preset_intent = check_for_env_settings()
            wake_word_sound_time = 0

            while True:
                pcm_frame = recorder.read()

                if not wake_word_detected:
                    if not should_wait_for_keyword:
                        wake_word_detected = True
                    else:
                        keyword_index = porcupine.process(pcm_frame)
                        if keyword_index >= 0:

                            continue


                    if wake_word_detected:
                        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        client.connect(str(SOCKET_PATH))
                        step_timer = time.time()

                elif intent is None:
                    if time.time() - step_timer > INTENT_TIMEOUT_S:
                        end_transcript('TIMEOUT')
                        continue

                    if preset_intent is not None:
                        intent = preset_intent
                    else:
                        rhino_is_finalized = rhino.process(pcm_frame)
                        if rhino_is_finalized:
                            intent = rhino.get_inference()

                    if intent is not None:
                        send_intent(intent)
                        step_timer = time.time()
                        if time.time() - wake_word_sound_time > 1.0:
                            play_sound(TRANSCRIPT_BEGIN_WAV)

                else:
                    if time.time() - step_timer > TRANSCRIPT_TIMEOUT_S:
                        end_transcript('TIMEOUT')
                        continue

                    partial_transcript, is_endpoint = cheetah.process(pcm_frame)
                    client.sendall((partial_transcript).encode())
                    if is_endpoint:
                        partial_transcript = cheetah.flush()
                        client.sendall((partial_transcript).encode())
                        end_transcript('STOP')
                        play_sound(TRANSCRIPT_SUCCESS_WAV)
                        time.sleep(0.3)

    except Exception as e:
        print(f"An error occured: {e}", file=sys.stderr)
    finally:
        should_continue = False
        if client is not None:
            client.sendall(b"<ERROR>")
            client.close()


if __name__ == '__main__':
    main()
