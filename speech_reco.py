import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import websocket
import base64
import pyaudio
import json
import os
from threading import Thread

nltk.download('punkt')
nltk.download('stopwords')

YOUR_API_TOKEN = os.getenv("ASSEMBLYAI_API_KEY")
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
p = pyaudio.PyAudio()

# starts recording
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=SAMPLE_RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

final_transcripts = []

def on_message(ws, message):
    """
    is being called on every message
    """
    global final_transcripts
    transcript = json.loads(message)
    text = transcript['text']

    if transcript['message_type'] == 'FinalTranscript':
        final_transcripts.append(text)


def on_error(ws, error):
    """
    is being called in case of errors
    """
    print(error)


def on_close(ws, close_status_code, close_msg):
    """
    is being called on session end
    """
    def clean_text(text):
        """
        Basic text cleaning and normalization.
        """
        tokens = word_tokenize(text)
        tokens = [word for word in tokens if word not in stopwords.words('english')]
        return ' '.join(tokens)

    cleaned_transcript = clean_text('\n'.join(final_transcripts))
    print("WebSocket closed")


def on_open(ws):
    """
    is being called on session begin
    """
    def send_data():
        while True:
            # read from the microphone
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

            # encode the raw data into base64 to send it over the websocket
            data = base64.b64encode(data).decode("utf-8")

            # Follow the message format of the Real-Time service (see documentation)
            json_data = json.dumps({"audio_data":str(data)})

            # Send the data over the wire
            ws.send(json_data)


    # Start a thread where we send data to avoid blocking the 'read' thread
    Thread(target=send_data).start()

# Set up the WebSocket connection with your desired callback functions
websocket.enableTrace(False)

# After opening the WebSocket connection, send an authentication header with your API token
auth_header = {"Authorization": f"{YOUR_API_TOKEN}" }

ws = websocket.WebSocketApp(
    f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}",
    header=auth_header,
    on_message=on_message,
    on_open=on_open,
    on_error=on_error,
    on_close=on_close
)

# Start the WebSocket connection
ws.run_forever()
