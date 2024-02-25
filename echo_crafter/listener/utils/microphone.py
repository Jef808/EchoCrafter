from contextlib import contextmanager

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
            sensitivities=[0.5],
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
            context_path=Config['RHINO_CONTEXT_FILE'],
            sensitivity=0.8
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
        self.wake_word_frame = None


    def get_next_frame(self):
        """Get the next frame from the recorder."""
        if self.wake_word_frame is not None:
            frame = self.wake_word_frame
            self.wake_word_frame = None
            return frame
        return self.recorder.read()


    def set_is_recording(self, is_recording):
        """Set the is_recording attribute of the recorder."""
        if self.recorder.is_recording and not is_recording:
            self.recorder.stop()
        elif not self.recorder.is_recording and is_recording:
            self.recorder.start()

    def wait_for_wake_word(self, wake_word_callback=None):
        """Wait for the wake word to be detected."""
        while self.recorder.is_recording:
            pcm_frame = self.recorder.read()
            keyword_index = self.porcupine.process(pcm_frame)
            if keyword_index >= 0:
                self.wake_word_frame = pcm_frame
                if wake_word_callback is not None:
                    wake_word_callback()
                break


    def infer_intent(self, on_intent_inferred):
        """Infer the user intent and pass it to the callback once collected."""
        while self.recorder.is_recording:
            pcm_frame = self.get_next_frame()
            rhino_is_finalized = self.rhino.process(pcm_frame)
            if rhino_is_finalized:
                intent = self.rhino.get_inference()
                on_intent_inferred(intent)
                break
        self.rhino.reset()


    def process_and_transmit_utterance(self, on_partial_transcript, on_final_transcript):
        """Process the utterance and pass the transcripts the callback."""
        is_endpoint = False
        is_transcription_success = False
        while self.recorder.is_recording:
            pcm_frame = self.get_next_frame()
            partial_transcript, is_endpoint = self.cheetah.process(pcm_frame)
            if is_endpoint:
                partial_transcript += (self.cheetah.flush())
                is_transcription_success = True
            on_partial_transcript(partial_transcript)
            if is_transcription_success:
                on_final_transcript()
                break


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
        mic.set_is_recording(True)
        yield mic
