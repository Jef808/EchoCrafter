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
import wave
from contextlib import closing

p = pyaudio.PyAudio()
##################
# # Audio config #
##################
#PIPEWIRE_DEVICE_INDEX = 7
DEFAULT_DEVICE = p.get_default_input_device_info()
DEFAULT_DEVICE_INDEX = DEFAULT_DEVICE['index']
SAMPLE_RATE = 16000 # int(DEFAULT_DEVICE['defaultSampleRate']) #16000
FRAMES_PER_BUFFER = SAMPLE_RATE // 5 #3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
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

# They both report time differently, so we compute the difference
# and store it here in order to work with normalized timestamps.
#_WEBSOCKET_TO_PYAUDIO_CLOCK_DIFF = None

# We use the following two to compute the above
#_PYAUDIO_TO_CLOCK_DIFF = None

# Buffers to store audio data and transcription results
WEB_SOCKET_IS_CONNECTING_BUFFER = []


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
        for data in self._buffer:
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


_LOGGER = Logger()
ws = None
FINAL_TRANSCRIPTS = []

# Set up the signal handler responsible for terminating the program at the end
def signal_handler(sig, frame):
    #global _PYAUDIO_END_TIME
    global _SHOULD_BE_RUNNING
    global _AAI_SESSION_END_REQUEST_TIME

    #_PYAUDIO_END_TIME = time.time()
    _SHOULD_BE_RUNNING = False
    print("Sending terminate_session to aai", file=sys.stderr)
    _AAI_SESSION_END_REQUEST_TIME = time.time()
    if ws is not None:
        try:
            ws.send(json.dumps({"terminate_session": True}))
        except Exception as e:
            print("Error while sending terminate_session: {e}", file=sys.stderr)
            p.terminate()

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

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
    _LOGGER.write(log_data)
    _LOGGER.record(in_data)

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
    current_time = time.time()
    pyaudio_buffer_time = time_info['input_buffer_adc_time']#) + _PYAUDIO_TO_CLOCK_DIFF
    pyaudio_current_time = time_info['current_time']#) + _PYAUDIO_TO_CLOCK_DIFF

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
    global _AAI_SESSION_START_TIME
    global _AAI_SESSION_END_TIME

    payload = json.loads(msg)
    message_type = payload['message_type']

    _LOGGER.write({"source": "ASSEMBLYAI", **payload})

    if message_type == 'SessionBegins':
        _AAI_SESSION_START_TIME = time.time()
        _LOGGER.setup(f"logs/{payload['session_id']}.log")

    elif message_type == 'FinalTranscript':
        FINAL_TRANSCRIPTS.append(payload)

    elif message_type == "SessionTerminated":
        _AAI_SESSION_END_TIME = time.time()
        ws.close()

########################
# Retrieve credentials #
########################
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
auth_header = {"Authorization": f"{API_KEY}"}

if not API_KEY:
    print("ERROR: Failed to retrieve ASSEMBLYAI_API_KEY env variable", file=sys.stderr)
    p.terminate()
    sys.exit(1)

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
        input_device_index=DEFAULT_DEVICE_INDEX,
        stream_callback=pyaudio_callback)
except Exception as e:
    print(f"Error while opening the pyaudio stream: {e}", file=sys.stderr)
    p.terminate()
    sys.exit(2)

_PYAUDIO_START_TIME = time.time()


def on_error(ws, *err):
    _LOGGER.write(*err)
    print(f"Error: {err}", file=sys.stderr)
########################
# Set up the websocket #
########################
try:
    ws = websocket.WebSocketApp(
        f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
        header=auth_header,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open)
except Exception as e:
    print(f"Error while initiating the websocket: {e}")
    stream.close()
    p.terminate()

#############################################################################
# Run until the program receives SIGINT, in which case it gracefully exists #
#############################################################################

with closing(_LOGGER):
    _AAI_SESSION_START_REQUEST_TIME = time.time()
    ec = ws.run_forever()
    print(' '.join(transcript['text'] for transcript in FINAL_TRANSCRIPTS))
    _LOGGER.write("\n**** SUMMARY *****\n"
                  f"SESSION_START: {_PYAUDIO_START_TIME}\n"
                  f"_AAI_SESSION_REQUEST: {_AAI_SESSION_START_REQUEST_TIME}\n"
                  f"_AAI_SESSION_START: {_AAI_SESSION_START_TIME}\n"
                  f"_AAI_SESSION_END_REQUEST: {_AAI_SESSION_END_REQUEST_TIME}\n"
                  f"_AAI_SESSION_END: {_AAI_SESSION_END_TIME}\n")

sys.exit(ec)
