from contextlib import contextmanager
from collections import deque
from pathlib import Path

import pvcheetah
import pvporcupine
import pvrhino
import pvrecorder

from echo_crafter.config import Config


@contextmanager
def porcupine_context_manager():
    """Create a Porcupine instance and yield it. Delete the instance upon exit."""
    porcupine_instance = None
    try:
        porcupine_instance = pvporcupine.create(
            keywords=['computer'],
            sensitivities=[0.1],
            access_key=Config['PICOVOICE_API_KEY']
        )
        yield porcupine_instance
    finally:
        if porcupine_instance is not None:
            porcupine_instance.delete()


@contextmanager
def cheetah_context_manager():
    """Create a Cheetah instance and yield it. Delete the instance upon exit."""
    cheetah_instance = None
    try:
        cheetah_instance = pvcheetah.create(
            access_key=Config['PICOVOICE_API_KEY'],
            endpoint_duration_sec=Config['ENDPOINT_DURATION_SEC'],
            model_path=Config['CHEETAH_MODEL_FILE']
        )
        yield cheetah_instance
    finally:
        if cheetah_instance is not None:
            cheetah_instance.delete()


@contextmanager
def recorder_context_manager():
    """Create a PvRecorder instance and yield it. Delete the instance upon exit."""
    recorder_instance = None
    try:
        recorder_instance = pvrecorder.PvRecorder(
            frame_length=Config['FRAME_LENGTH']
        )
        yield recorder_instance
    finally:
        if recorder_instance is not None:
            if recorder_instance.is_recording:
                recorder_instance.stop()
            recorder_instance.delete()


@contextmanager
def rhino_context_manager():
    """Create a PvRecorder instance and yield it. Delete the instance upon exit."""
    rhino_instance = None
    try:
        rhino_instance = pvrhino.create(
            access_key=Config['PICOVOICE_API_KEY'],
            context_path=Config['RHINO_CONTEXT_FILE']
        )
        yield rhino_instance
    finally:
        if rhino_instance is not None:
            rhino_instance.delete()


class _Microphone:
    """A class implementing the various microphone actions we use."""

    def __init__(self, porcupine, rhino, cheetah, recorder):
        self.porcupine = porcupine
        self.rhino = rhino
        self.cheetah = cheetah
        self.recorder = recorder
        self.is_listening = False
        self.wake_word_frame = None


    def get_next_frame(self):
        """Get the next frame from the recorder."""
        if self.wake_word_frame is not None:
            frame = self.wake_word_frame
            self.wake_word_frame = None
            return frame
        return self.recorder.read()


    def set_is_listening(self, is_listening):
        """Set the is_listening attribute of the recorder."""
        self.is_listening = is_listening
        if is_listening and not self.recorder.is_recording:
            self.recorder.start()
        elif not is_listening and self.recorder.is_recording:
            self.recorder.stop()

    def wait_for_wake_word(self, wake_word_callback=None):
        """Wait for the wake word to be detected."""
        while True:
            pcm_frame = self.recorder.read()
            keyword_index = self.porcupine.process(pcm_frame)
            if keyword_index >= 0:
                self.wake_word_frame = pcm_frame
                if wake_word_callback is not None:
                    wake_word_callback()
                break


    def process_and_transmit_utterance(self, transcription_callback, transcription_success_callback=None):
        """Process the utterance and transmit the partial transcript to the client."""
        is_endpoint = False
        is_transcription_success = False
        while not is_endpoint:
            pcm_frame = self.get_next_frame()
            partial_transcript, is_endpoint = self.cheetah.process(pcm_frame)
            if is_endpoint:
                partial_transcript += (self.cheetah.flush() + 'STOP')
                is_transcription_success = True
            transcription_callback(partial_transcript)
            if is_transcription_success and transcription_success_callback is not None:
                    transcription_success_callback()


@contextmanager
def microphone():
    """A context manager taking care of never leaking any resource."""
    with porcupine_context_manager() as porcupine, \
         cheetah_context_manager() as cheetah, \
         rhino_context_manager() as rhino, \
         recorder_context_manager() as recorder:
        mic = _Microphone(porcupine,
                          rhino,
                          cheetah,
                          recorder)
        mic.set_is_listening(True)
        yield mic
