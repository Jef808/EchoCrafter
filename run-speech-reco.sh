#!/usr/bin/env sh

ASSEMBLYAI_API_KEY=$(pass assemblyai.com/api_key) /usr/bin/python ./speech-to-text/speech_reco.py 2>/dev/null
