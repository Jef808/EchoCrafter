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
import threading


##################
# # Audio config #
##################
SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
PIPEWIRE_DEVICE_INDEX = 13
##############################
# # Termination logic config #
##############################
# Global flag indicating when to initiate the termination logic
_RUNNING = True

# Timeout in seconds before we fallback to pyaudio.paAbort
_STREAM_CLEANUP_TIMEOUT = 3

# Fallback if toggling the above times out
_STREAM_CLEANUP_TIMEOUT_PASSED = False

# Indicator while waiting for assemblyAI to terminate the session
_WEBSOCKET_IS_ACTIVE = False

# Timeout in seconds before we forcefully close the websocket while waiting
_WEBSOCKET_CLEANUP_TIMEOUT = 3

def signal_handler(sig, frame):
    global _RUNNING
    _RUNNING = False  # Signal to PyAudio to stop processing

    def timeout_elapsed(start_time, duration):
        return time.time() - start_time > duration

    # Wait for PyAudio stream to be inactive or timeout
    time_start = time.time()
    while stream.is_active() and not timeout_elapsed(time_start, _STREAM_CLEANUP_TIMEOUT):
        time.sleep(0.1)

    # Attempt to close PyAudio stream
    # # NOTE: toggling the flag here makes our stream callback
    # ignore any new data anyway.
    try:
        if stream.is_active():
            _STREAM_CLEANUP_TIMEOUT_PASSED = True
            stream.stop_stream()
        stream.close()
    except Exception as e:
        print(f"Error on pyaudio stream cleanup: {e}", file=sys.stderr)

    # Signal to AssemblyAI to close the session
    ws.send(json.dumps({"terminate_session": True}))

    # Wait for WebSocket to close or timeout
    time_start = time.time()
    while _WEBSOCKET_IS_ACTIVE and not timeout_elapsed(ws_timeout_start, _WEBSOCKET_CLEANUP_TIMEOUT):
        time.sleep(0.1)

    p.terminate()  # Terminate PyAudio


# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)


# Correctly format and send data to both `ws` and `logger` endpoints
def send_data(ws, in_data, frame_count, time_info, status):
    data = {"audio_data": base64.b64encode(in_data).decode("utf-8")}
    ws.send(json.dumps(data))

    # Print all data for logging
    meta_data = {
        "frame_count": frame_count,
        "time_info": time_info,
        "status": status
    }
    print(json.dumps(meta_data), file=sys.stderr)


# This callback is used by pyaudio's stream to handle the collected
# audio data. It runs in a separate thread.
def pyaudio_callback(in_data, frame_count, time_info, status):
    if _WEBSOCKET_IS_ACTIVE:
        if status != pyaudio.paNoError and frame_count > 0:
            print(f"Stream error: {status}", file=sys.stderr)
        if _STREAM_CLEANUP_TIMEOUT_PASSED:
            print(f"Pyaudio cleanup timeout is passed, ignoring its feed", file=sys.stderr)
            return (None, pyaudio.paAbort)
        send_data(ws, in_data, frame_count, time_info, status)
    if _RUNNING:
        return (None, pyaudio.paContinue)
    else:
        return (None, pyaudio.paComplete)


####################################################
# The pyaudio stream reading the microphone device #
####################################################
p = pyaudio.PyAudio()
stream = p.open(
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
    global _WEBSOCKET_IS_ACTIVE
    _WEBSOCKET_IS_ACTIVE = True

def on_close(ws, ec, err):
    global _WEBSOCKET_IS_ACTIVE
    _WEBSOCKET_IS_ACTIVE = False

def on_message(ws, msg):
    payload = json.loads(msg)
    if not payload['text']:
        return
    if payload['message_type'] == 'PartialTranscript':
        print(f"[PARTIAL TRANSCRIPT]: {payload['text']}")
    elif payload['message_type'] == 'FinalTranscript':
        print(f"[FINAL TRANSCRIPT]:   {payload['text']}")


API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
auth_header = {"Authorization": f"{API_KEY}"}

ws = websocket.WebSocketApp(
    f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
    header=auth_header,
    on_message=on_message,
    on_error=lambda ws, err: print(err, file=sys.stderr),
    on_close=on_close,
    on_open=on_open)


#############################################################################
# Run until the program receives SIGINT, in which case it gracefully exists #
#############################################################################
ws.run_forever()

print("All sessions terminated and resources cleaned up", file=sys.stderr)
