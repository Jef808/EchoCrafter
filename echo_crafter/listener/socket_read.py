"""Listen for wake word and transcribe speech to text."""

from echo_crafter.logger import setup_logger

from collections import deque
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

SOCKET_PATH = Path(os.getenv('XDG_RUNTIME_DIR')) / "transcription"
n_connections = 0

logger = setup_logger()
intent = ''
intent_args = dict()
partial_transcripts_queue = deque()
partial_transcripts = []


def handle_final_transcript():
    """Log the transcript."""
    final_transcript = ''.join(partial_transcripts)
    partial_transcripts.clear()

    logger.info(final_transcript, intent=intent, slots=intent_args)


def handle_partial_transcript():
    """Send partial transcript to the active window."""
    partial_transcript = partial_transcripts_queue.popleft()
    partial_transcripts.append(partial_transcript)

    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', partial_transcript]
    )


def get_special_token(content):
    """Return the special token if it exists in the content."""
    idx_beg = content.find('<')
    if idx_beg >= 0:
        idx_end = idx_beg+1 + content[idx_beg+1:].find('>')
        if idx_end > idx_beg:
            return idx_beg, content[idx_beg:idx_end+1]
    return None


def handle_client(client_socket, client_address):
    """Handle a client connection."""
    global n_connections
    global intent
    global intent_args

    content_string = ""
    rhino_s = ""

    try:
        while True:
            content_bytes = client_socket.recv(1024)
            if not content_bytes:
                break

            content_string += content_bytes.decode()

            special_token = get_special_token(content_string)
            if special_token is not None:
                beg, token = special_token
                if token in ('<ERROR>', '<TIMEOUT>'):
                    break

                if token == '<STOP>':
                    if beg > 0:
                        partial_transcripts_queue.append(content_string[:beg])
                        handle_partial_transcript()
                    handle_final_transcript()
                    break

                if token == '<RHINO_BEGIN>':
                    if beg > 0:
                        raise RuntimeError("<RHINO_BEGIN> found in the middle of a transcript")
                    idx_beg = len('<RHINO_BEGIN>')
                    rhino_end = get_special_token(content_string[idx_beg+1:])
                    if rhino_end is None:
                        continue
                    if rhino_end[1] != '<RHINO_END>':
                        raise RuntimeError("<RHINO_BEGIN> found without a matching <RHINO_END>")
                    idx_end = idx_beg + rhino_end[0] + 1
                    rhino_s = content_string[idx_beg: idx_end]
                    rhino = json.loads(rhino_s)
                    intent = rhino.get('intent', 'unknown')
                    intent_args = rhino.get('slots', {})
                    content_string = content_string[idx_end + len('<RHINO_END>'):]

            if content_string:
                partial_transcripts_queue.append(content_string)
                handle_partial_transcript()
                content_string = ""

    except RuntimeError as e:
        print(f"Oops! {e}", file=sys.stderr)
    except Exception as e:
        print(f"{__file__}: {json.dumps(e.__dict__)}", file=sys.stderr)

    finally:
        client_socket.close()


def main():
    """Listen for connections and handle them."""
    try:
        SOCKET_PATH.unlink()
    except OSError:
        if SOCKET_PATH.exists():
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(str(SOCKET_PATH))
        server_socket.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                if n_connections > 0:
                    client_socket.close()
                else:
                    handle_client(client_socket, client_address)
        finally:
            SOCKET_PATH.unlink()


if __name__ == '__main__':
    main()
