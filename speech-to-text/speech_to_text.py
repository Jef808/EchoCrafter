#!/usr/bin/env python3
from transformers import pipeline
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
import numpy as np
import torch
import sys

SILENCE_THRESHOLD = 0.01  # Threshold for silence detection
SILENCE_DURATION = 1.2    # Duration of silence to consider as end-of-speech (seconds)
CHUNK = 3200              # Number of audio frames per buffer


device = "cuda:0" if torch.cuda.is_available() else "cpu"
classifier = pipeline(
    "audio-classification", model="mit/ast-finetuned-speech-commands-v2", device=device
)


def launch_fn(
    wake_word="marvin",
    prob_threshold=0.8,
    chunk_length_s=2.0,
    stream_chunk_s=0.2,
    debug=False,
):
    if wake_word not in classifier.model.config.label2id.keys():
        raise ValueError(
            f"Wake word {wake_word} not in set of valid class labels, pick a wake word in the set {classifier.model.config.label2id.keys()}."
        )

    sampling_rate = classifier.feature_extractor.sampling_rate

    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )

    print("Listening for wake word...", file=sys.stderr)
    for prediction in classifier(mic):
        prediction = prediction[0]
        if debug:
            print(prediction, file=sys.stderr)
        if prediction["label"] == wake_word:
            if prediction["score"] > prob_threshold:
                return True


def transcribe(chunk_length_s=10.0, stream_chunk_s=1.0, *, debug=False):
    transcriber = pipeline(
        "automatic-speech-recognition", model="openai/whisper-small.en", device=device
    )

    sampling_rate = transcriber.feature_extractor.sampling_rate

    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )

    print("Listening for command...", file=sys.stderr)
    for item in transcriber(mic, generate_kwargs={"max_new_tokens": 128}):
        if (debug):
            print(item["text"], end="\n", file=sys.stderr)
        if not item["partial"][0]:
            break

    return item["text"]


if __name__ == '__main__':
    launch_fn(debug=False)
    transcription = transcribe()
    print(transcription)
