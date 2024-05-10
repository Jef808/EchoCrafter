"""Utility functions for the echo_crafter module."""

import math
from echo_crafter.config import Config


def get_utterance(*,
                  audio_buffer,
                  vad,
                  frame_length,
                  sample_rate,
                  stop_event):
    """Get an utterance from the audio buffer."""
    utterance = []
    frame_length_sec = frame_length * 2 / sample_rate
    endpoint_duration = Config['ENDPOINT_DURATION_SEC']
    endpoint_num_frames = math.ceil(endpoint_duration / frame_length_sec)

    n_silent_frames = -1

    while True:
        utterance.extend(audio_buffer.get())
        voice_probability = vad.process(utterance[-frame_length:])

        if n_silent_frames >= 0 and voice_probability < 0.1:
            n_silent_frames += 1
        elif voice_probability > 0.12:
            n_silent_frames = 0

        if (n_silent_frames == endpoint_num_frames or stop_event()):
            break
    return utterance
