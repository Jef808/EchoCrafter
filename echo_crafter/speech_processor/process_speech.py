import copy
import threading
import time
from queue import Queue
from collections import deque
from contextlib import ExitStack
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from .resources import *

logger = setup_logger(__name__)


class Recorder(threading.Thread):
    def __init__(self, buffer):
        super().__init__()
        self._buffer = buffer
        self._is_recording = False
        self._stop = False
        self._pause = False
        self._pcm = list()

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        with create_recorder(frame_length=Config['FRAME_LENGTH']) as recorder:
            recorder.start()
            time.sleep(0.25)

            while not self._stop:
                pcm_frame = recorder.read()
                if not self._pause:
                    self._buffer.put(pcm_frame)
            recorder.stop()

            self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass
        return self._pcm

    def clear_buffer(self):
        self.pause()
        with self._buffer.mutex:
            self._buffer.queue.clear()
        self._pcm.clear()
        self.resume()

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def reset(self):
        self.clear_buffer()
        self._stop = False
        self._pause = False


class VoiceCommander:
    """Voice Commander class."""

    def __init__(self, *,
                 on_wake_word,
                 on_intent_success,
                 on_intent_failure,
                 wake_word="computer",
                 wake_word_sensitivity=0.5,
                 intent_sensitivity=0.7,
                 end_of_speech_timeout=1.3,
                 ):
        self.pv = {}
        with ExitStack() as stack:
            self.pv['cobra'](stack.enter_context(create_cobra()))
            self.pv['porcupine'](stack.enter_context(create_porcupine(wake_word=wake_word, sensitivity=wake_word_sensitivity)))
            self.pv['rhino'](stack.enter_context(create_rhino(context_file=Config['RHINO_CONTEXT_FILE'], sensitivity=intent_sensitivity)))
            self.pv['leopard'](stack.enter_context(create_leopard(model_file=Config['LEOPARD_MODEL_FILE'])))

            stack.pop_all()

        self.on_wake_word = on_wake_word
        self.on_intent_success = on_intent_success
        self.on_intent_failure = on_intent_failure
        self.buffer = Queue()
        self.recorder = Recorder(self.buffer)
        self.pcm = list()
        self.end_of_speech_timeout = end_of_speech_timeout

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, _):
        if self.recorder is not None:
            self.recorder.stop()
        if exc_type:
            logger.error(f"An error occurred: {exc_value}", exc_info=True)
        return False

    def start(self):
        """Main loop."""
        self.recorder.start()
        while True:
            self.wait_for_wake_word()
            inference = self.infer_intent()
            if inference.is_understood:
                self.on_intent_success({"intent": inference.intent, "slots": inference.slots})
            else:
                self.transcribe()
            self.reset()

    def wait_for_wake_word(self):
        """Wait for the wake word to be detected."""
        while True:
            pcm_frame = self.buffer.get()
            keyword = self.pv['porcupine'].process(pcm_frame)
            if keyword >= 0:
                self.on_wake_word()
                self.recorder.clear_buffer()

    def infer_intent(self):
        """Infer the intent from the audio frames.

        Here we buffer the audio frames in case intent inference
        fails and we need to transcribe the audio.
        """
        while True:
            pcm_frame = self.buffer.get()
            is_finalized = self.pv['rhino'].process(pcm_frame)
            if is_finalized:
                inference = self.pv['rhino'].get_intent()
                return inference

    def _detect_beginning_of_speech(self):
        """Detect the beginning of speech.

        This function uses VAD to detect the start of speech.
        Returns the number of frames after the wake word before speech was detected.
        """
        frames_before_speech = 0
        while True:
            pcm_frame = self.buffer.get()
            voice_probability = self.pv['cobra'].process(pcm_frame)
            if voice_probability < 0.3:
                frames_before_speech += 1
            else:
                break
        return frames_before_speech

    def _detect_end_of_speech(self):
        """Detect the end of speech event according to `self.end_of_speech_timeout`.

        This function uses VAD to detect the end of speech.
        Returns the number of frames during which speech was detected.
        """
        time_since_last_voice = 0
        frames_before_end_of_speech = 0
        while True:
            pcm_frame = self.buffer.get()
            voice_probability = self.pv['cobra'].process(pcm_frame)
            if voice_probability < 0.2:
                time_since_last_voice += 0.1  # frames consist of 100ms of audio
            else:
                time_since_last_voice = 0
            if time_since_last_voice < self.end_of_speech_timeout:
                frames_before_end_of_speech += 1
            else:
                break
        return frames_before_end_of_speech

    def transcribe(self):
        """Transcribe utterance using Speech-to-Text engine.

        This function is called when the intent inference fails.
        It uses VAD to detect the start and end of speech then passes
        the corresponding audio frames to the Speech-to-Text engine.

        Args:
            pcm_data: A list of audio frames.

        Returns:
            str: The transcribed text.
            dict: The start and end the confidence score.
        """
        frames_begin = self._detect_beginning_of_speech()
        number_of_frames = self._detect_end_of_speech()
        self.recorder.stop()
        pcm_speech = self.pcm[frames_begin: frames_begin + number_of_frames + 1]
        transcript, words = self.pv['leopard'].process(pcm_speech)
        self.on_intent_failure(transcript, words)

    def transcribe(self):

        def get_utterance():
            """Get the utterance from the buffered audio frames.

            This function is called when the intent inference fails.
            It uses VAD to detect the start and end of speech.
            """
            time_since_last_voice = 0
            _pcm = []
            while True:
                pcm_frame = self.frames.get()
                voice_probability = self.pv['cobra'].process(pcm_frame)
                if voice_probability > 0.3:
                    break

            while True:

                _pcm.append(pcm_frame)

                    return _pcm

        threading.Thread(target=get_utterance).start()

        while True:
            pcm_frame = self.pv['recorder'].read()
            self.frames.put(pcm_frame[:])
            self.buffer.append(pcm_frame)
            if self.is_buffer_full():
                self.pv['recorder'].stop()
                self.pv['recorder'].start()
                return self._transcribe_buffer()

    def _wait_for_end_of_speech(self, buffer):
        # Implement: Detect end of speech based on the audio frames
        while True:
            if self.is_buffer_full():
            pcm_frame = buffer.popleft()
            voice_probability = self.pv['cobra'].process(pcm_frame)
            if voice_probability > 0.3:
                return False
            return True

    def set_state(self, state):
        self.state = state
        if state == 'recognizing_intent':
            self.is_buffering = True
        elif state == 'finished':
            self.reset()

    def reset(self):
        # Implement: Reset state and buffer
        self.pv.reset()

    def is_buffer_full(self):
        # Implement based on a predefined limit or buffer property
        return len(self.buffer) == self.buffer.maxlen
