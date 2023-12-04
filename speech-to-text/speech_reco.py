"""listens to the microphone and generate a transcript of the english speech.

To terminate the process, use Ctrl-C in the terminal (send SIGINT).

It is printed to stdout, and any other output of the program is sent to stderr.
"""

import websocket
import base64
import pyaudio
import json
import os
import io
import time
import sys
import signal

#
##################
# # Audio config #
##################
SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
PIPEWIRE_DEVICE_INDEX = 10
##############################
# # Termination logic config #
##############################
# Global flag indicating when to initiate the termination logic
_RUNNING = False
_SESSION_END_TIME = None

# Timeout in seconds before we fallback to pyaudio.paAbort
_STREAM_CLEANUP_TIMEOUT = 3

# Fallback if toggling the above times out
_STREAM_CLEANUP_TIMEOUT_PASSED = False

# Indicator while waiting for assemblyAI to terminate the session
_WEBSOCKET_IS_ACTIVE = False

# Timeout in seconds before we forcefully close the websocket while waiting
_WEBSOCKET_CLEANUP_TIMEOUT = 3

_LOGGER = None
ws = None


# Set up the signal handler responsible for terminating the program at the end
def signal_handler(sig, frame):
    global _RUNNING
    _RUNNING = False  # Signal to PyAudio to stop processing


# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)


# Correctly format and send data to both `ws` and `logger` endpoints
# NOTE: We will never send data to a websocket before it is ready since
# the stream is started in the websocket's on_open callback.
def send_data(ws, in_data, frame_count, time_info, status):
    data = {"audio_data": base64.b64encode(in_data).decode("utf-8")}
    ws.send(json.dumps(data))

    log_data = {
        "PYAUDIO": {
            "in_data": "<<blob>>",
            "frame_count": frame_count,
            "time_info": time_info,
            "status": status
        }
    }
    # Print all data for logging
    print(json.dumps(log_data), file=_LOGGER)


# This callback is used by pyaudio's stream to handle the collected
# audio data. It runs in a separate thread.
def pyaudio_callback(in_data, frame_count, time_info, status):
    if not _RUNNING:
        # At the end of a session, process audio frames until timestamp
        # is past the session end time, then close websocket
        global _SESSION_END_TIME
        if not _SESSION_END_TIME:
            _SESSION_END_TIME = time_info['current_time']
        elif time_info['input_buffer_adc_time'] > _SESSION_END_TIME:
            ws.send(json.dumps({"terminate_session": True}))
            ws.close()
            return (None, pyaudio.paComplete)
    send_data(ws, in_data, frame_count, time_info, status)
    return (None, pyaudio.paContinue)


#################################
# Create and start audio stream #
#################################

p = pyaudio.PyAudio()

def open_stream():
    return p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER,
        input_device_index=PIPEWIRE_DEVICE_INDEX,
        stream_callback=pyaudio_callback)

#################################################################
# Setup the websocket connecting to the assemblyAI api endpoint #
#################################################################
def on_open(ws):
    global stream
    stream = open_stream()

def on_close(ws, ec, err):
    global _WEBSOCKET_IS_ACTIVE
    _WEBSOCKET_IS_ACTIVE = False
    stream.stop_stream()
    stream.close()
    p.terminate()

def on_message(ws, msg):
    payload = json.loads(msg)
    if payload['message_type'] == "SessionBegins":
        global _WEBSOCKET_IS_ACTIVE
        _WEBSOCKET_IS_ACTIVE = True

    if 'text' in payload and payload['message_type'] == 'FinalTranscript':
        # Print the valuable responses to stdout
        print(payload['text'])

    print(json.dumps({"ASSEMBLYAI": payload}), file=_LOGGER)

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
        on_error=lambda ws, err: print(err, file=_LOG_PATHNAME),
        on_close=on_close,
        on_open=on_open)

#############################################################################
# Run until the program receives SIGINT, in which case it gracefully exists #
#############################################################################

with open('logs/stt.log', 'w') as _LOGGER:
    _RUNNING = True
    ec = ws.run_forever()

exit(ec)
