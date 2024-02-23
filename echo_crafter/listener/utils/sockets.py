import socket
import contextlib

# Define a context manager for the socket connection
@contextlib.contextmanager
def socket_connection(socket_path):
    """Create a socket connection to the server."""
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(socket_path)
        yield client
    finally:
        client.close()
