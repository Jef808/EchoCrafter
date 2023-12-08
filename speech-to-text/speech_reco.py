"""listens to the microphone and generate a transcript of the english speech.

To terminate the process, use Ctrl-C in the terminal (send SIGINT).

It is printed to stdout, and any other output of the program is sent to stderr.
"""

import websocket
import base64
import pyaudio
import json
import os
import time
import sys
import signal
from contextlib import closing

p = pyaudio.PyAudio()
##################
# # Audio config #
##################
PIPEWIRE_DEVICE_INDEX = 7
DEFAULT_DEVICE = p.get_default_input_device_info()
DEFAULT_DEVICE_INDEX = DEFAULT_DEVICE['index']
SAMPLE_RATE = int(DEFAULT_DEVICE['defaultSampleRate']) #16000
FRAMES_PER_BUFFER = 9600 #3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
##############################
# # Termination logic config #
##############################

# Time when recording starts
_SESSION_START_TIME = None

# Time when recording stops
_SESSION_END_TIME = None

# Time when websocket's connection is established
_WEBSOCKET_CONNECTION_TIME = None

# Time when assemblyAI considers the session to start
_WEBSOCKET_SESSION_START_TIME = None

# Time when assemblyAI considers the session over
_WEBSOCKET_SESSION_END_TIME = None

# They both report time differently, so we compute the difference
# and store it here in order to work with normalized timestamps.
_WEBSOCKET_TO_PYAUDIO_CLOCK_DIFF = None

# We use the following two to compute the above
_PYAUDIO_TO_CLOCK_DIFF = None

# Buffers to store audio data and transcription results
WEB_SOCKET_IS_LOADING_BUFFER = []


class Logger:
    def __init__(self):
        self._logger = None
        self._buffer = []

    def close(self):
        self._logger.close()

    def setup(self, filepath):
        self._logger = open(filepath, 'w+')
        for message in self._buffer:
            self._logger.write(message)
        self._buffer = []

    def write(self, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        if self._logger is None:
            self._buffer.append(message)
        else:
            self._logger.write(message)


_LOGGER = Logger()
ws = None
FINAL_TRANSCRIPTS = []

# Set up the signal handler responsible for terminating the program at the end
def signal_handler(sig, frame):
    global _SESSION_END_TIME
    _SESSION_END_TIME = time.time()

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

# Correctly format and send data to both `ws` and `logger` endpoints
# NOTE: We will never send data to a websocket before it is ready since
# the stream is started in the websocket's on_open callback.
def send_data(ws, in_data, frame_count, pyaudio_buffer_time, pyaudio_current_time, current_time):
    global WEB_SOCKET_IS_LOADING_BUFFER

    data = {"audio_data": base64.b64encode(in_data).decode("utf-8")}

    json_data = json.dumps(data)

    if _WEBSOCKET_CONNECTION_TIME is None:
        WEB_SOCKET_IS_LOADING_BUFFER.append(json_data)
        return

    if len(WEB_SOCKET_IS_LOADING_BUFFER) > 0:
        for data in WEB_SOCKET_IS_LOADING_BUFFER:
            ws.send(data)
        WEB_SOCKET_IS_LOADING_BUFFER = []

    log_data = {
        "source": "PYAUDIO",
        "frame_count": frame_count,
        "buffer_time": pyaudio_buffer_time,
        "pyaudio_current_time": pyaudio_current_time,
        "current_time": current_time
    }

    # Print all data for logging
    _LOGGER.write(log_data)

    ws.send(json_data)

# This callback is used by pyaudio's stream to handle the collected
# audio data. It runs in a separate thread.
def pyaudio_callback(in_data, frame_count, time_info, status):
    global _PYAUDIO_TO_CLOCK_DIFF

    if _PYAUDIO_TO_CLOCK_DIFF is None:
        _PYAUDIO_TO_CLOCK_DIFF = time.time() - float(time_info['current_time'])

    pyaudio_buffer_time = float(time_info['input_buffer_adc_time']) + _PYAUDIO_TO_CLOCK_DIFF
    pyaudio_current_time = float(time_info['current_time']) + _PYAUDIO_TO_CLOCK_DIFF
    current_time = time.time()

    send_data(ws, in_data, frame_count, pyaudio_buffer_time, pyaudio_current_time, current_time)

    if _SESSION_END_TIME is not None:
        # At the end of a session, process audio frames until timestamp
        # is past the session end time, then close websocket
        if pyaudio_buffer_time > _SESSION_END_TIME:
            ws.send(json.dumps({"terminate_session": True}))
            return (None, pyaudio.paComplete)

    return (None, pyaudio.paContinue)


#################################
# Create and start audio stream #
#################################
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER,
    input_device_index=DEFAULT_DEVICE_INDEX,
    stream_callback=pyaudio_callback)

_SESSION_START_TIME = time.time()


#################################################################
# Setup the websocket connecting to the assemblyAI api endpoint #
#################################################################
def on_open(ws):
    global _WEBSOCKET_CONNECTION_TIME
    _WEBSOCKET_CONNECTION_TIME = time.time()
    _LOGGER.write("WEBSOCKET CONNECTION WITH ASSEMBLYAI ESTABLISHED")

def on_close(ws, ec, err):
    try:
        if not stream.is_stopped(): stream.stop_stream()
    finally:
        stream.close()
        p.terminate()

# TODO: Simply consider PYAUDIO_TO_WEBSOCKET to be
# \[
#     \Delta = time.time() - pyaudio.current_time - session_begin_time
# \]
# where time.time() and pyaudio.current_time represent the same time point (now)
def on_message(ws, msg):
    global FINAL_TRANSCRIPTS
    global _WEBSOCKET_SESSION_START_TIME
    global _WEBSOCKET_SESSION_END_TIME
    global _PYAUDIO_TO_WEBSOCKET_DIFF
    global _LOGGER

    payload = json.loads(msg)
    message_type = payload['message_type']

    if message_type == 'SessionBegins':
        _LOGGER.setup(f"logs/{payload['session_id']}.log")
        _WEBSOCKET_SESSION_START_TIME = time.time()
        _PYAUDIO_TO_WEBSOCKET_DIFF = _WEBSOCKET_SESSION_START_TIME - _PYAUDIO_TO_CLOCK_DIFF
        _LOGGER.write(payload)

    elif message_type == 'PartialTranscript':
        _LOGGER.write(payload)

    elif message_type == 'FinalTranscript':
        FINAL_TRANSCRIPTS.append(payload)
        _LOGGER.write(payload)

    elif message_type == "SessionTerminated":
        _WEBSOCKET_SESSION_END_TIME = time.time()
        ws.close()

    _LOGGER.write({"source": "ASSEMBLYAI", **payload})

########################
# Retrieve credentials #
########################
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
auth_header = {"Authorization": f"{API_KEY}"}

########################
# Set up the websocket #
########################
ws = websocket.WebSocketApp(
        f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
        header=auth_header,
        on_message=on_message,
        on_error=lambda ws, err: _LOGGER.write(err),
        on_close=on_close,
        on_open=on_open)

#############################################################################
# Run until the program receives SIGINT, in which case it gracefully exists #
#############################################################################

with closing(_LOGGER):
    ec = ws.run_forever()
    print(' '.join(transcript['text'] for transcript in FINAL_TRANSCRIPTS))

exit(ec)
