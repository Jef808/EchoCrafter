#!/usr/bin/env python

"""listens to the microphone and generate a transcript of the english speech.

To terminate the process, use Ctrl-C in the terminal (send SIGINT).

It is printed to stdout, and any other output of the program is sent to stderr.
"""

import subprocess
import websocket
import base64
import pyaudio
import json
import os
import time
import sys
import signal
import wave
import requests
from contextlib import closing
import argparse

parser = argparse.ArgumentParser(description='Handle command line arguments')
parser.add_argument('--input-device', type=int, help='Input device ID')
parser.add_argument('--sample-rate', type=int, help='Input device sample rate')
parser.add_argument('--frames-per-buffer', type=int, help='Frames per buffer')
parser.add_argument('--format', type=str, help='Format of the audio')
parser.add_argument('--channels', type=int, help='Number of audio channels')

args = parser.parse_args()

p = None

##############################
# # Termination logic config #
##############################

# Time when recording starts
_PYAUDIO_START_TIME = None

# Time when recording stops
_PYAUDIO_END_TIME = None

_SHOULD_BE_RUNNING = True

# When the websocket connection is initiated
_AAI_SESSSION_START_REQUEST_TIME = None

# Time when assemblyAI considers the session to start
_AAI_SESSION_START_TIME = None

# When the terminate_session message was sent
_AAI_SESSION_END_REQUEST_TIME = None

# Number of seconds to wait before closing websocket
_AAI_SESSION_END_TIMEOUT = 5

# Time when assemblyAI answers with a SessionTerminated message
_AAI_SESSION_END_TIME = None

# Buffers to store audio data and transcription results
WEB_SOCKET_IS_CONNECTING_BUFFER = []

ws = None
stream = None
RUNNING_PARTIAL_TRANSCRIPT = ""
TRANSCRIPT = []

class Logger:
    def __init__(self):
        self._logger = None
        self._wav_file = None
        self._buffer = []
        self._wav_buffer = []
        self._start = time.time()
        self.write(f"SESSION START: {time.time()}")

    def close(self):
        self.write(f"SESSION END: {time.time()}\n")
        if self._logger is not None:
            self._logger.close()
        if self._wav_file is not None:
            self._wav_file.close()
        if len(self._buffer) > 0 or len(self._wav_buffer) > 0:
            print("WARNING: closing buffer with non empty buffer", file=sys.stderr)

    def setup(self, filepath):
        self._logger = open(f"{filepath}.log", 'w+')
        self._wav_file = wave.open(f"{filepath}.wav", 'wb')
        self._wav_file.setnchannels(1)
        self._wav_file.setsampwidth(2)
        self._wav_file.setframerate(SAMPLE_RATE)
        for message in self._buffer:
            self.write(message)
        self._buffer = []
        for data in self._wav_buffer:
            self.record(data)
        self._wav_buffer = []

    def write(self, message):
        if not isinstance(message, str):
            message = json.dumps(message)
        if self._logger is None:
            self._buffer.append(message)
        else:
            self._logger.write(message + '\n')

    def record(self, data):
        if self._wav_file is None:
            self._wav_buffer.append(data)
        else:
            self._wav_file.writeframes(data)


#_LOGGER = Logger()
#
# Correctly format and send data to both `ws` and `logger` endpoints
# NOTE: We will never send data to a websocket before it is ready since
# the stream is started in the websocket's on_open callback.
def send_data(ws, in_data, frame_count, pyaudio_buffer_time, pyaudio_current_time, current_time):
    global WEB_SOCKET_IS_CONNECTING_BUFFER

    data = {"audio_data": base64.b64encode(in_data).decode("utf-8")}

    json_data = json.dumps(data)

    log_data = {
        "source": "PYAUDIO",
        "frame_count": frame_count,
        "buffer_time": pyaudio_buffer_time,
        "pyaudio_current_time": pyaudio_current_time,
        "current_time": current_time
    }

    # Print all data for logging
    # _LOGGER.write(log_data)
#    _LOGGER.record(in_data)

    if _AAI_SESSION_START_TIME is None:
        WEB_SOCKET_IS_CONNECTING_BUFFER.append(json_data)
        return

    if len(WEB_SOCKET_IS_CONNECTING_BUFFER) > 0:
        for data in WEB_SOCKET_IS_CONNECTING_BUFFER:
            ws.send(data)
        WEB_SOCKET_IS_CONNECTING_BUFFER = []

    ws.send(json_data)

# This callback is used by pyaudio's stream to handle the collected
# audio data. It runs in a separate thread.
def pyaudio_callback(in_data, frame_count, time_info, status):
    global _PYAUDIO_START_TIME

    current_time = time.time()
    pyaudio_buffer_time = time_info['input_buffer_adc_time']#) + _PYAUDIO_TO_CLOCK_DIFF
    pyaudio_current_time = time_info['current_time']#) + _PYAUDIO_TO_CLOCK_DIFF

    if _PYAUDIO_START_TIME is None:
        _PYAUDIO_START_TIME = current_time
        print("microphone listening...", file=sys.stderr)

    send_data(ws, in_data, frame_count, pyaudio_buffer_time, pyaudio_current_time, current_time)

    if not _SHOULD_BE_RUNNING:
        return (None, pyaudio.paComplete)

    return (None, pyaudio.paContinue)


#################################################################
# Setup the websocket connecting to the assemblyAI api endpoint #
#################################################################
def on_open(ws):
    global _AAI_SESSSION_BEGIN_TIME
    _AAI_SESSSION_BEGIN_TIME = time.time()

def on_close(ws, ec, err):
    print("closing websocket connection", file=sys.stderr)
    if RUNNING_PARTIAL_TRANSCRIPT:
        TRANSCRIPT.append(RUNNING_PARTIAL_TRANSCRIPT)
    if not stream.is_stopped():
        stream.close()
        p.terminate()


def handle_on_message(text, message_type, running_partial_transcript):
    global _AAI_SESSION_END_REQUEST_TIME

    _running_partial_transcript = running_partial_transcript
    _utterance = ""

    if message_type == "FinalTranscript":
        if running_partial_transcript:
            _utterance += _running_partial_transcript
        _running_partial_transcript = ""
        if _AAI_SESSION_END_REQUEST_TIME is not None:
            ws.close()

    # If text is expanding on the running partial transcript
    elif text.startswith(_running_partial_transcript):
        _running_partial_transcript = text
        if _AAI_SESSION_END_REQUEST_TIME is not None:
            ws.close()

    # If text is the beginning of a new utterance
    else:
        _utterance += _running_partial_transcript
        _running_partial_transcript = text

    return _running_partial_transcript, _utterance


def on_message(ws, msg):
    global _AAI_SESSION_START_TIME
    global RUNNING_PARTIAL_TRANSCRIPT
    global TRANSCRIPT

    payload = json.loads(msg)
    message_type = payload['message_type']

    if message_type == 'SessionBegins':
        _AAI_SESSION_START_TIME = time.time()
#        _LOGGER.setup(f"/home/jfa/projects/echo-crafter/logs/{payload['session_id']}")
        return

    if  message_type == 'SessionTerminated':
        ws.close()

    text = payload['text']

    if not text:
        return

    RUNNING_PARTIAL_TRANSCRIPT, utterance = handle_on_message(text, message_type, RUNNING_PARTIAL_TRANSCRIPT)
    if utterance:
        TRANSCRIPT.append(utterance)

#    _LOGGER.write({"RUNNING_PARTIAL_TRANSCRIPT": text, "created": payload['created']})

def on_error(ws, *err):
#    _LOGGER.write(*err)
    print(f"Error: {err}", file=sys.stderr)

########################
# Set up the websocket #
########################
def get_api_key():
    p_api_key = subprocess.run(["pass", "assemblyai.com/api_key"], capture_output=True)
    if not p_api_key.stdout:
        print("ERROR: Failed to retrieve assemblyai.com/api_key pass entry", file=sys.stderr)
        if not stream.is_stopped(): stream.close()
        p.terminate()
        sys.exit(3)
    return str(p_api_key.stdout, encoding="utf-8").strip()

def main():
    global p
    global stream
    global ws

    p = pyaudio.PyAudio()

    ##################
    # # Audio config #
    ##################
    DEFAULT_DEVICE = p.get_default_input_device_info()
    DEFAULT_DEVICE_INDEX = DEFAULT_DEVICE['index']
    SAMPLE_RATE = int(DEFAULT_DEVICE['defaultSampleRate']) # 16000
    FRAMES_PER_BUFFER = int(SAMPLE_RATE)  # Sync AssemblyAI's throughput of twice a second
    LATENCY = FRAMES_PER_BUFFER / SAMPLE_RATE
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    DEVICE_INDEX = DEFAULT_DEVICE_INDEX

    # Set up the signal handler responsible for terminating the program at the end
    def signal_handler(sig, frame):
        #global _PYAUDIO_END_TIME
        global _SHOULD_BE_RUNNING
        global _AAI_SESSION_END_REQUEST_TIME

        time.sleep(LATENCY)
        _SHOULD_BE_RUNNING = False
        print("Sending terminate_session to aai", file=sys.stderr)

        _AAI_SESSION_END_REQUEST_TIME = time.time()
        if ws is not None:
            try:
                ws.send(json.dumps({"terminate_session": True}))
            except Exception as e:
                print(f"Error while sending terminate_session: {e}", file=sys.stderr)
                p.terminate()

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    #################################
    # Create and start audio stream #
    #################################
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            input_device_index=DEVICE_INDEX,
            stream_callback=pyaudio_callback)
    except Exception as e:
        print(f"Error while opening the pyaudio stream: {e}", file=sys.stderr)
        p.terminate()
        sys.exit(7)

    try:
        ws = websocket.WebSocketApp(
            f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
            header={"Authorization": get_api_key()},
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open)
    except Exception as e:
        print(f"Error while initiating the websocket: {e}", file=sys.stderr)
        if not stream.is_stopped():
            stream.close()
            p.terminate()

    #############################################################################
    # Run until the program receives SIGINT, in which case it gracefully exists #
    #############################################################################
    #with closing(_LOGGER):
    _AAI_SESSION_START_REQUEST_TIME = time.time()
    ec = ws.run_forever()

    _AAI_SESSION_END_TIME = time.time()

    time_to_wrap_up = _AAI_SESSION_END_TIME - _AAI_SESSION_END_REQUEST_TIME
    transcript = ' '.join(TRANSCRIPT)
    print(transcript)

        # _LOGGER.write("{SUMMARY: "
        #               f"SESSION_START: {_PYAUDIO_START_TIME}, "
        #               f"AAI_SESSION_REQUEST: {_AAI_SESSION_START_REQUEST_TIME}, "
        #               f"AAI_SESSION_START: {_AAI_SESSION_START_TIME}, "
        #               f"AAI_SESSION_END_REQUEST: {_AAI_SESSION_END_REQUEST_TIME}, "
        #               f"AAI_SESSION_END: {_AAI_SESSION_END_TIME}"
        #               "}")
        # _LOGGER.write(f"TIME_TO_WRAP_UP: {time_to_wrap_up}")
        # _LOGGER.write(json.dumps({"transcript": transcript}))

    sys.exit(ec)

if __name__ == '__main__':
    main()
