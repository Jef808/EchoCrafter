"""Read from a socket and send the data to the active window."""

from pathlib import Path
import socket
import subprocess
from echo_crafter.config import Config


queue = []

def handle_partial_transcript(partial_transcript):
    """Send partial transcript to the active window."""
    subprocess.Popen(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', partial_transcript]
    )


def handle_client(client_socket, _):
    """Handle a client connection."""
    try:
        got_final_transcript = False
        while not got_final_transcript:
            partial_transcript = client_socket.recv(1024)
            if not partial_transcript:
                break
            partial_transcript_s = partial_transcript.decode()
            if partial_transcript_s.endswith('STOP'):
                partial_transcript_s = partial_transcript_s[:-4] + ' '
                got_final_transcript = True
            handle_partial_transcript(partial_transcript_s)

    finally:
        client_socket.close()


def main():
    """Listen for connections and handle them."""
    socket_path = Path(Config['SOCKET_PATH'])
    try:
        socket_path.unlink()
    except OSError:
        if socket_path.exists():
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(Config['SOCKET_PATH'])
        server_socket.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                handle_client(client_socket, client_address)
        finally:
            socket_path.unlink()


if __name__ == '__main__':
    main()
