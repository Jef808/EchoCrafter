#!/usr/bin/env python3

import math
import time
import wave
import struct
from resources import (
    create_recorder,
    create_porcupine,
    create_rhino,
    create_cobra,
    create_leopard
)
from collections import deque
from queue import Empty, Queue
from tabulate import tabulate
from threading import Event, Thread
from contextlib import ExitStack, contextmanager
from echo_crafter.commander import intent_handler
from echo_crafter.logger import setup_logger
from echo_crafter.config import Config
from echo_crafter.utils import play_sound

logger = setup_logger(__name__)


class VoiceAssistant:
    """A voice assistant that listens for a wake word and processes audio for intent recognition."""

    def __init__(self, *,
                 wake_word="Echo-crafter",
                 wake_word_sensitivity=0.4,
                 intent_sensitivity=0.6,
                 max_utterance_duration_sec=5.0):
        self.wake_words = [wake_word]
        self.max_utterance_duration_sec = max_utterance_duration_sec
        self.audio_buffer = Queue()
        self.pv = {}
        self.intent_handler = intent_handler.initialize()
        with ExitStack() as stack:
            self.voice_activity_detector = stack.enter_context(create_cobra())
            self.wake_word_detector = stack.enter_context(create_porcupine(wake_word=wake_word, sensitivity=wake_word_sensitivity))
            self.speech_to_intent = stack.enter_context(create_rhino(context_file=Config['RHINO_CONTEXT_FILE'], sensitivity=intent_sensitivity))
            self.speech_to_text = stack.enter_context(create_leopard(model_file=Config['LEOPARD_MODEL_FILE']))
            self.recorder = stack.enter_context(create_recorder())
            self.shut_down = stack.pop_all().close

    def run(self):
        """Starts the voice assistant."""
        try:
            while True:
                self.reset()
                self.wait_for_wake_word()
                self.wait_for_intent(save="intent_utterance.wav")
        finally:
            self.shut_down()

    def is_recording(self):
        """Returns whether the voice assistant is currently recording."""
        return self.recorder.is_recording

    def get_frame_length_sec(self):
        """Returns the frame length in seconds."""
        return self.recorder.frame_length * 2 / self.recorder.sample_rate

    def wait_for_wake_word(self, num_frames_to_keep: int = 8):
        """Listens for the wake word and starts processing when detected.

        Args: num_frames_to_keep: The number of trailing frames to prepend to the next step's buffer
              in order to not have a gap of "dropped frames" between "wake-word-detected" and beginning of
              "intent-inference" steps.

        This can be explained as follows: It takes about 10 frames of 1024 bytes for me to say "Echo-crafter" at 16kHz.
        If say the wake-word detection engine requires 60% of the total audio time of the wake-word to detect it, then
        detection will actually occur 6 frames after the wake-word is done being spoken. Those frames will be lost unless
        we save them and prepend them to the next step's buffer.
        """
        _buffer = deque()
        while self.is_recording():
            if len(_buffer) == num_frames_to_keep:
                _buffer.popleft()

            pcm_frame = self.recorder.read()
            _buffer.append(pcm_frame)

            keyword = self.wake_word_detector.process(pcm_frame)
            if keyword >= 0:
                play_sound(Config['WAKE_WORD_DETECTED_WAV'])
                for frame in _buffer:
                    self.audio_buffer.put_nowait(frame)
                break

    def wait_for_intent(self, *, save=None):
        """Infer the intent from the audio frames.

        Here we buffer the audio frames in case intent inference
        fails and we need to transcribe the audio.
        """
        while self.is_recording():
            pcm_frame = self.recorder.read()
            self.audio_buffer.put_nowait(pcm_frame)

            if self.speech_to_intent.process(pcm_frame):
                inference = self.speech_to_intent.get_inference()
                if inference.is_understood:
                    play_sound(Config['INTENT_SUCCESS_WAV'])
                    self.handle_intent(inference)
                else:
                    with self.audio_buffering():
                        utterance = self.get_utterance()
                        transcript, words = self.speech_to_text.process(utterance)
                        print("Got transcription...")
                        if save:
                            self.save_utterance(utterance, save)
                        self.handle_transcription(transcript, words)
                break

    @contextmanager
    def audio_buffering(self):
        """Buffers audio frames for processing in a separate thread."""
        stop_event = Event()

        def _do_buffer_audio():
            while not stop_event.is_set():
                self.audio_buffer.put_nowait(self.recorder.read())

        t = Thread(target=_do_buffer_audio)
        try:
            t.start()
            yield

        finally:
            stop_event.set()
            t.join(0.5)
            if t.is_alive():
                raise RuntimeError("Failed to stop buffering thread")

    def get_utterance(self) -> list[int]:
        """Detect the end of speech.

        This function uses VAD to detect the end of speech.
        Returns the number of frames during which speech was detected.
        """
        utterance = list()

        # Compute the number of silent frames to wait before ending the utterance
        frame_length_sec = self.get_frame_length_sec()
        num_frames = math.ceil(Config['ENDPOINT_DURATION_SEC'] / frame_length_sec)

        n_silent_frames = -1
        time_start = time.time()

        while self.is_recording():
            utterance.extend(self.audio_buffer.get())
            voice_probability = self.voice_activity_detector.process(utterance[-self.recorder.frame_length:])

            if n_silent_frames >= 0 and voice_probability < 0.1:
                n_silent_frames += 1
            elif voice_probability > 0.12:
                n_silent_frames = 0

            if (n_silent_frames == num_frames
                or (n_silent_frames < 0 and time.time() - time_start > self.max_utterance_duration_sec)
            ):
                break
        return utterance


    def reset(self):
        """Resets the state of the voice assistant.

        Note: it is necessary to stop and start the recorder instance in order to
        flush its inner circular buffer.
        """
        self.speech_to_intent.reset()
        self._pause_recorder()
        self._flush_audio_buffer()
        self._resume_recorder()

    def _pause_recorder(self):
        """Pauses the recorder."""
        if self.is_recording():
            self.recorder.stop()
        while self.is_recording():
            pass

    def _resume_recorder(self):
        """Resumes the recorder."""
        if not self.is_recording():
            self.recorder.start()

    def _flush_audio_buffer(self):
        """Flushes the audio buffer."""
        while True:
            try:
                self.audio_buffer.get_nowait()
            except Empty:
                break

    def save_utterance(self, utterance: list[int], file_path: str) -> None:
        """Saves the utterance to a WAV file."""
        with wave.open(file_path, 'wb') as wf:
            wf.setparams((1, 2, 16000, 512, "NONE", "NONE"))
            wf.writeframes(struct.pack("h" * len(utterance), *utterance))

    def handle_intent(self, inference):
        """Handles the processing of recognized intents."""
        self.intent_handler(intent=inference.intent, slots=inference.slots)

    def handle_transcription(self, transcript, words):
        """Handles the processing of transcriptions."""
        print(transcript)
        print(tabulate(
            words,
            headers=['word', 'start_sec', 'end_sec', 'confidence', 'speaker_tag'],
            floatfmt='.2f'))

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
