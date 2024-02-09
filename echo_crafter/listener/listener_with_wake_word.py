"""Listen for a wake word, then transcribe speech."""

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

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT'))
DATA_DIR = PROJECT_ROOT / "data"
CHEETAH_MODEL_FILE = DATA_DIR / "speech-command-cheetah-v1.pv"
PORCUPINE_LAPTOP_KEYWORD_FILE = DATA_DIR / "laptop_en_linux_v3_0_0.ppn"
RHINO_CONTEXT_FILE = DATA_DIR / "computer-commands_en_linux_v3_0_0.rhn"
TRANSCRIPT_BEGIN_WAV = DATA_DIR / "transcript_begin.wav"
TRANSCRIPT_SUCCESS_WAV = DATA_DIR / "transcript_success.wav"
SOCKET_PATH = Path(os.getenv('XDG_RUNTIME_DIR')) / "transcription"

INTENT_TIMEOUT_S = 5
TRANSCRIPT_TIMEOUT_S = 15


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
    """Create a Cheetah instance and yield it. Delete the instance upon exit."""
    rhino_instance = None
    try:
        rhino_instance = pvrhino.create(
            access_key=os.getenv('PICOVOICE_API_KEY'),
            context_path=str(RHINO_CONTEXT_FILE),
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
    subprocess.Popen(["aplay", "-q", str(wav_file)])


def make_check_for_env_settings():
    """Monitor the environment for changes and update the relevant globals accordingly."""
    last_should_wait_for_keyword_s = ''
    last_intent_s = ''
    last_slots_s = ''
    should_wait_for_keyword = True
    preset_intent = None

    def check_for_env_settings():
        nonlocal last_should_wait_for_keyword_s
        nonlocal last_intent_s
        nonlocal last_slots_s
        nonlocal should_wait_for_keyword
        nonlocal preset_intent

        _should_wait_for_keyword_s = os.getenv('ECHO_CRAFTER_WAIT_FOR_KEYWORD') or ''
        _intent_s = os.getenv('ECHO_CRAFTER_INTENT') or ''
        _slots_s = os.getenv('ECHO_CRAFTER_INTENT_SLOTS') or ''

        if _should_wait_for_keyword_s != last_should_wait_for_keyword_s:
            last_should_wait_for_keyword_s = _should_wait_for_keyword_s
            should_wait_for_keyword = _should_wait_for_keyword_s.lower() == 'false'

        if _intent_s != last_intent_s or _slots_s != last_slots_s:
            last_intent_s = _intent_s
            last_slots_s = _slots_s if _intent_s else ''

            intent = [True, _intent_s, {}] if _intent_s else None
            if _slots_s:
                slots_kv_s = _slots_s.split(',')
                try:
                    intent[2] = {k: v for k, v in (e.split('=') for e in slots_kv_s)}
                except ValueError:
                    print("ECHO_CRAFTER_INTENT_SLOTS should be a comma separated list of 'key=value' entries", file=sys.stderr)
                    intent = None
            preset_intent = intent

        return should_wait_for_keyword, preset_intent

    return check_for_env_settings


def main():
    """Upon detection of a wake word, transcribe speech until endpoint is detected."""
    global should_continue

    keywords = ["computer"]
    keyword_paths = [PORCUPINE_LAPTOP_KEYWORD_FILE]
    keyword_paths.extend(pvporcupine.KEYWORD_PATHS[w] for w in keywords)
    keywords = [Path(w).stem.split('_')[0] for w in keyword_paths]
    sensitivity = 0.1
    sensitivities = [sensitivity] * len(keyword_paths)
    device_index = -1
    frame_length = 512
    client = None

    check_for_env_settings = make_check_for_env_settings()

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
                            wake_word_detected = True
                            play_sound(TRANSCRIPT_BEGIN_WAV)
                            wake_word_sound_time = time.time()

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
