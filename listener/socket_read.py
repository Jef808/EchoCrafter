#!/usr/bin/env python3

import socket
import os
import subprocess

SOCKET_PATH = "/tmp/transcript_socket"
n_connections = 0


def handle_partial_transcript(partial_transcript):
    """Send partial transcript to the active window."""
    subprocess.run(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '0', partial_transcript]
    )


def handle_client(client_socket, client_address):
    """Handle a client connection."""
    global n_connections
    n_connections += 1

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
        n_connections -= 1


def main():
    """Listen for connections and handle them."""
    try:
        os.unlink(SOCKET_PATH)
    except OSError:
        if os.path.exists(SOCKET_PATH):
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(SOCKET_PATH)
        server_socket.listen(1)

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                if n_connections > 0:
                    client_socket.close()
                else:
                    handle_client(client_socket, client_address)
        finally:
            os.unlink(SOCKET_PATH)


if __name__ == '__main__':
    main()
