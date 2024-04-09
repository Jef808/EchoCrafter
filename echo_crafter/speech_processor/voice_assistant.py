#!/usr/bin/env python3

import time
import wave
import json
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
from echo_crafter.speech_processor.utils import utils

logger = setup_logger(__name__)


class VoiceAssistant:
    """A voice assistant that listens for a wake word and processes audio for intent recognition."""

    def __init__(self, *,
                 wake_word="Echo-crafter",
                 wake_word_sensitivity=0.5,
                 intent_sensitivity=0.5,
                 max_utterance_duration_sec=5.0):
        self.wake_words = [wake_word]
        self.max_utterance_duration_sec = max_utterance_duration_sec
        self.wake_word_detected_time =  None
        self.audio_buffer = Queue()
        self.intent_handler = intent_handler.initialize()
        with ExitStack() as stack:
            self.voice_activity_detector = stack.enter_context(create_cobra())
            self.wake_word_detector = stack.enter_context(create_porcupine(wake_word=wake_word, sensitivity=wake_word_sensitivity))
            self.speech_to_intent = stack.enter_context(create_rhino(context_file=Config['RHINO_CONTEXT_FILE'], sensitivity=intent_sensitivity))
            self.speech_to_text = stack.enter_context(create_leopard(model_file=Config['LEOPARD_MODEL_FILE']))
            self.recorder = stack.enter_context(create_recorder())
            self.shut_down = stack.pop_all().close

    def run(self):
        """Start the voice assistant in the current thread."""
        try:
            while True:
                self.reset()
                self.wait_for_wake_word()
                self.wait_for_intent(save="intent_utterance.wav")
        finally:
            self.shut_down()

    def is_recording(self):
        """Check whether the voice assistant is currently recording."""
        return self.recorder.is_recording

    def get_frame_length_sec(self):
        """Compute the frame length in seconds in terms of the frame length and the sample rate."""
        return self.recorder.frame_length * 2 / self.recorder.sample_rate

    def wait_for_wake_word(self, num_frames_to_keep: int = 12):
        """Listen for the wake word amongst the incoming audio frames.

        Args: num_frames_to_keep: The number of trailing frames to add to the buffer once the wake word is detected.
              This is done in order to not have a gap within the sequence of frames between a "wake-word-detected" event
              and the beginning of the "intent-inference" step.

        This can be explained as follows: It takes me about 600ms to say "Echo-crafter" (the default wake word). At 1024 bytes per frame and
        16kHz sample rate, this corresponds to 10 frames. Suppose it takes the wake-word detection engine about 300ms to detect a spoken wake-word. Then
        we the detection will only happen about 5 frames after the wake-word was spoken. Those frames will be lost, unless we save them and prepend them
        to the audio buffer for the next processing step.
        """
        _buffer = deque(maxlen=num_frames_to_keep)
        print("waiting for wake word...")
        while self.is_recording():
            pcm_frame = self.recorder.read()
            _buffer.append(pcm_frame)

            keyword = self.wake_word_detector.process(pcm_frame)
            if keyword >= 0:
                play_sound(Config['WAKE_WORD_DETECTED_WAV'])
                for frame in _buffer:
                    self.audio_buffer.put_nowait(frame)
                self.wake_word_detected_time = time.time()
                break

    def wait_for_intent(self, *, save=None):
        """Infer the intent from the incoming audio frames.

        In a loop, we process the incoming audio frames (from the audio buffer) with our speech-to-intent engine.
        Once we get an inference, we check if it is understood. If it is, we handle the intent and slots.
        If not, we transcribe the audio until the end of the user's utterance and handle the transcription
        which is sent to the transcription handler.
        """
        print("waiting for intent...")
        with self.audio_buffering():
            while self.is_recording():
                pcm_frame = self.audio_buffer.get()

                if self.speech_to_intent.process(pcm_frame):
                    inference = self.speech_to_intent.get_inference()
                    if inference.is_understood:
                        print(json.dumps(inference, indent=2))
                        play_sound(Config['INTENT_SUCCESS_WAV'])
                        self.handle_intent(inference)
                    else:
                        print("Intent not understood, transcribing...")
                        stop_event = lambda: (
                            (self.wake_word_detected_time and
                             time.time() - self.wake_word_detected_time > self.max_utterance_duration_sec) or
                            self.audio_buffer.empty() and not self.is_recording()
                        )
                        utterance = utils.get_utterance(
                            audio_buffer=self.audio_buffer,
                            vad=self.voice_activity_detector,
                            frame_length=self.recorder.frame_length,
                            sample_rate=self.recorder.sample_rate,
                            stop_event=stop_event
                        )
                        transcript, words = self.speech_to_text.process(utterance)
                        print("Got transcription...")
                        if save:
                            self.save_utterance(utterance, save)
                        self.handle_transcription(transcript, words)
                    break

    @contextmanager
    def audio_buffering(self):
        """Buffer incoming audio frames in a separate thread.

        This is useful for processing audio frames from a buffer and backtracking to previous
        frames in case we want to (e.g. in case of a failed intent inference).
        """
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

    def reset(self):
        """Reset the state of the voice assistant.

        This includes the speech-to-intent engine's internal state, the audio buffer,
        the recorder's internal buffer, along with any variables used for tracking
        the speech processor's current state."""
        self.speech_to_intent.reset()
        self._pause_recorder()
        self._flush_audio_buffer()
        self._resume_recorder()
        self.wake_word_detected_time = None

    def _pause_recorder(self):
        """Pause the recorder.

        Note: When pausing and resuming the recorder, its internal buffer gets flushed."""
        if self.is_recording():
            self.recorder.stop()
        while self.is_recording():
            pass

    def _resume_recorder(self):
        """Resume the recorder.

        Note: When pausing and resuming the recorder, its internal buffer gets flushed."""
        if not self.is_recording():
            self.recorder.start()

    def _flush_audio_buffer(self):
        """Flush the audio buffer."""
        self.audio_buffer.queue.clear()

    def save_utterance(self, utterance: list[int], file_path: str) -> None:
        """Save the utterance to a WAV file.

        Note: The utterance is a list of regular integers, but the format at which we sample
        audio and save it to the WAV file is as a sequence of signed 16-bit integers.
        Therefore, we need to pack them two at a time before writing them to the WAV file."""
        with wave.open(file_path, 'wb') as wf:
            wf.setparams((1, 2, 16000, 512, "NONE", "NONE"))
            wf.writeframes(struct.pack("h" * len(utterance), *utterance))

    def handle_intent(self, inference):
        """Handle a recognized speech-to-intent inference.

        We pass the intent and slots as they are generated by the speech-to-intent engine.
        Further processing is done within the intent handler.
        """
        self.intent_handler(intent=inference.intent, slots=inference.slots)

    def handle_transcription(self, transcript, words):
        """Handle a transcription for the speech that was not recognized by the speech-to-intent engine."""
        print(transcript)
        print(tabulate(
            words,
            headers=['word', 'start_sec', 'end_sec', 'confidence', 'speaker_tag'],
            floatfmt='.2f'))

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
