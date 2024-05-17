"""Transcribe a prerecorded audio file using the Deepgram API."""

import json
import httpx
import struct
import logging
from typing import List
from datetime import datetime
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    BufferSource,
)
from echo_crafter.config import Config
#from echo_crafter.logger import setup_logger

#setup_logger(__name__)
logger = logging.getLogger(__name__)


class Deepgram(DeepgramClient):
    """Deepgram client wrapper."""

    @staticmethod
    def make_options(config: dict) -> PrerecordedOptions:
        model = config['DEEPGRAM_MODEL'],
        language = config['DEEPGRAM_LANGUAGE'],
        smart_format = config['DEEPGRAM_SMART_FORMAT'],
        features = config['DEEPGRAM_FEATURES'] or [],
        custom_intent = config['DEEPGRAM_CUSTOM_INTENT'],
        custom_topic = config['DEEPGRAM_CUSTOM_TOPIC'],

        options_dict = {
            "model": config['DEEPGRAM_MODEL'],
        }
        if language is not None:
            options_dict.update(language=language)
        if smart_format is not None:
            options_dict['smart_format'] = True
        if 'intents' in features:
            options_dict['intents'] = True
        if 'topics' in features:
            options_dict['topics'] = True
        if 'summarize' in features:
            options_dict['summarize'] = 'v2'
        # if features is not None:
        #     for feature in features:
        #         options_dict[feature] = 'true'
        # if custom_intent:
        #     options_dict['custom_intents'] = custom_intents
        # if custom_topics:
        #     options_dict['custom_topics'] = custom_topics

        logger.info("Options dict:")
        logger.info(json.dumps(options_dict, indent=4))

        return PrerecordedOptions(**options_dict)

    def __init__(self, *, access_key: str):
        """Initialize the Deepgram client."""
        super().__init__(api_key=access_key)
        self.options = self.make_options(Config)

        logger.info("Initialized Deepgram client with following options")
        logger.info(json.dumps(self.options.to_dict(), indent=4))

    def process(self, pcm: List[int]) -> List[object]:
        """Transcribe the given audio data."""
        buffer_data = struct.pack('h' * len(pcm), *pcm)
        payload: BufferSource = {"buffer": buffer_data}
        response = self.listen.prerecorded.v("1").transcribe_file(payload, self.options)
        logger.info(response.to_json(indent=4))
        transcript = response.results.channels[0].alternatives[0].transcript
        words = response.results.channels[0].alternatives[0].words

        return transcript, words

def create(*, access_key: str):
    return Deepgram(access_key=access_key)


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], "rb") as f:
        _data = f.read()

    lang = sys.argv[2] if len(sys.argv) > 2 else None

    transcript = transcribe(_data, language=lang)
    logger.info(transcript)
