from echo_crafter.config import Config

from contextlib import contextmanager
import pvcheetah
import pvporcupine
import pvrecorder

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
        recorder_instance.start()
        yield recorder_instance
    finally:
        if recorder_instance is not None:
            recorder_instance.delete()


class _Microphone:
    """A context manager for the recorder_context_manager."""

    def __init__(self, recorder, porcupine, cheetah):
        self.recorder = recorder
        self.porcupine = porcupine
        self.cheetah = cheetah

    def wait_for_wake_word(self):
        """Wait for the wake word to be detected."""
        while True:
            pcm_frame = self.recorder.read()
            keyword_index = self.porcupine.process(pcm_frame)
            if keyword_index >= 0:
                break

    def process_and_transmit_utterance(self, client):
        """Process the utterance and transmit the partial transcript to the client."""
        while True:
            pcm_frame = self.recorder.read()
            partial_transcript, is_endpoint = self.cheetah.process(pcm_frame)
            client.sendall((partial_transcript).encode())
            if is_endpoint:
                partial_transcript = self.cheetah.flush()
                client.sendall((partial_transcript + 'STOP').encode())
                break


@contextmanager
def Microphone():
    """Create a Microphone instance and yield it. Delete the instance upon exit."""
    with recorder_context_manager() as recorder, porcupine_context_manager() as porcupine, cheetah_context_manager() as cheetah:
        mic = _Microphone(recorder, porcupine, cheetah)
        yield mic
