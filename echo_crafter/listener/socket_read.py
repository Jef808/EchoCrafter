from echo_crafter.config import Config

from pathlib import Path
import socket
import subprocess

def handle_partial_transcript(partial_transcript):
    """Send partial transcript to the active window."""
    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', partial_transcript]
    )


def handle_client(client_socket, _):
    """Handle a client connection."""
    try:
        while True:
            partial_transcript = client_socket.recv(1024)
            if not partial_transcript:
                break
            partial_transcript_s = partial_transcript.decode()
            if partial_transcript_s.endswith('STOP'):
                partial_transcript_s = partial_transcript_s[:-4]
                handle_partial_transcript(partial_transcript_s)
                break
            else:
                handle_partial_transcript(partial_transcript_s)
    finally:
        client_socket.close()


def main():
    """Listen for connections and handle them."""
    SOCKET_PATH = Path(Config['SOCKET_PATH'])
    try:
        SOCKET_PATH.unlink()
    except OSError:
        if SOCKET_PATH.exists():
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(Config['SOCKET_PATH'])
        server_socket.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                handle_client(client_socket, client_address)
        finally:
            SOCKET_PATH.unlink()


if __name__ == '__main__':
    main()
