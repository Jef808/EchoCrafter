"""listens to the microphone and generate a transcript of the english speech.

To terminate the process, use Ctrl-C in the terminal (send SIGINT).
The result is in the form of a JSON object

    {
      "result": "TRANSCRIBED SPEECH",
      "error":  "ERROR MESSAGE (IF ANY)"
    }.

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
from threading import Thread

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not API_KEY:
    print("No environment variable named ASSEMBLYAI_API_KEY found.", file=sys.stderr)
    sys.exit(1)

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
p = pyaudio.PyAudio()
ws_app = None
send_data_thread = None
done = False
SECONDS_BEFORE_EXIT = 2.5

# starts recording
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=SAMPLE_RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

last_partial_transcript = ''
final_transcripts = []
result = ''
error = ''

time_since_last_input = 0

def on_message(ws, message):
    """
    is being called on every message
    """
    global last_partial_transcript
    global final_transcript
    transcript = json.loads(message)
    message_type = transcript['message_type']

    if message_type == 'SessionBegins':
        return

    text = transcript['text']

    if message_type == 'PartialTranscript':
        last_partial_transcript = text
    elif transcript['message_type'] == 'FinalTranscript':
        final_transcripts.append(last_partial_transcript)
        print(''.join(final_transcripts), file=sys.stderr)
        last_partial_transcript = ''


def on_error(ws, error):
    """
    is being called in case of errors
    """
    sys.exit(1)

def on_close(ws, close_status_code, close_msg):
    """
    is being called on session end
    """
    global result
    global error

    error = close_msg
    result = ''.join(final_transcripts)

def on_open(ws):
    """
    is being called on session begin
    """
    global send_data_thread
    global done

    def send_data():
        while not done:
            # read from the microphone
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

            # encode the raw data into base64 to send it over the websocket
            data = base64.b64encode(data).decode("utf-8")

            # Follow the message format of the Real-Time service (see documentation)
            json_data = json.dumps({"audio_data":str(data)})

            # Send the data over the wire
            ws.send(json_data)

    print("Websocket connection to AssemblyAI api initiated", file=sys.stderr)

    # Start a thread where we send data to avoid blocking the 'read' thread
    send_data_thread = Thread(target=send_data)
    send_data_thread.start()

def start():
    global ws_app

    # Set up the WebSocket connection with your desired callback functions
    websocket.enableTrace(False)

    # After opening the WebSocket connection, send an authentication header with your API token
    auth_header = {"Authorization": f"{API_KEY}" }
    ws_app = websocket.WebSocketApp(
        f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
        header=auth_header,
        on_message=on_message,
        on_open=on_open,
        on_error=on_error,
        on_close=on_close
    )
    # Start the WebSocket connection
    ws_app.run_forever()

def stop():
    global done
    print(f"Exiting in {SECONDS_BEFORE_EXIT} seconds...", file=sys.stderr)

    start_timer = time.process_time()

    done = True
    send_data_thread.join()

    elapsed_time = time.process_time() - start_timer

    time.sleep(max(0, SECONDS_BEFORE_EXIT - elapsed_time))

    ws_app.close()

def signal_handler(signal, frame):
    stop()

ws_thread = Thread(target=start)

ws_thread.start()

signal.signal(signal.SIGINT, signal_handler)

ws_thread.join()

print(json.dumps({'result': result, 'error': error}))
