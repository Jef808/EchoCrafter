import threading
import time
from collections import deque
from contextlib import ExitStack
from echo_crafter.config import Config
from echo_crafter.logger import setup_logger
from .resources import *

logger = setup_logger(__name__)


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
            self.pv['recorder'](stack.enter_context(create_recorder(frame_length=Config['FRAME_LENGTH'])))

            stack.pop_all()

        super().__init__()
        self.on_wake_word = on_wake_word
        self.on_intent_success = on_intent_success
        self.on_intent_failure = on_intent_failure
        self.buffer = deque([], maxlen=Config['BUFFER_SIZE'])
        self.state = 'idle'
        self.frames_processed_for_eos = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.error(f"An error occurred: {exc_value}", exc_info=True)
        return False

    def start(self):
        """Process the audio frames."""
        pcm_frame = self.pv['recorder'].read()
        self.process_frame(pcm_frame)

    def get_next_frame(self):
        if self.state in ['recognizing_intent', 'search_for_endpoint']:
            if len(self.buffer) > self.frames_processed_for_eos:
                pcm_frame = self.state[self.frames_processed_for_eos]
            else:
                pcm_frame = self.pv['rhino'].read()

    def process_frame(self, pcm_frame):
        if self.is_buffering:
            self.buffer.append(pcm_frame)

        if self.state == 'idle':
            time.sleep(0.08)  # Implement: Adjust according to needs
        elif self.state == 'wait_for_wake_word':
            keyword = self.pv['porcupine'].process(pcm_frame)
            if keyword >= 0:
                self.set_state('recognizing_intent')
                self.buffer.append(pcm_frame)
                
                # TODO: Figure out if this helps
                self.pv['recorder'].stop()
                self.pv['recorder'].start()
        elif self.state == 'recognizing_intent':
            is_finalized = self.pv['rhino'].process(pcm_frame)
            if is_finalized:
                inference = self.pv['rhino'].get_intent()
                if inference.is_understood:
                    self.on_intent_success({"intent": inference.intent, "slots": inference.slots})
                    self.set_state('finished')
                else:
                    self.on_intent_failure()
                    self.set_state('search_for_endpoint')
        elif self.state == 'wait_for_eos':
            if self._detect_end_of_speech():
                self.set_state('finished')

    def _detect_end_of_speech(self, buffer):
        # Implement: Detect end of speech based on the audio frames
        while buffer:
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
