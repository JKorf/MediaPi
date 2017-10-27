import socket
import urllib.request

from Shared.Settings import Settings


class TcpClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        if self.port == 0:
            self.port = 6881
        self.socket = None
        self.con_timeout = Settings.get_int("connection_timeout") / 1000

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.con_timeout)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)
            return True
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return False

    def send(self, data):
        try:
            self.socket.sendall(data)

            return True
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return False

    def receive_available(self, max):
        try:
            return bytes(self.socket.recv(max))
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return None

    def receive(self, expected):
        buffer = bytearray()
        total_received = 0
        while total_received < expected:
            try:
                received_bytes = self.socket.recv(expected - total_received)
            except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
                return None

            if received_bytes is None or len(received_bytes) == 0:
                return None

            buffer.extend(received_bytes)
            total_received += len(received_bytes)
        return bytes(buffer)

    def disconnect(self):
        if self.socket is not None:
            self.socket.close()


class UdpClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.con_timeout = Settings.get_int("connection_timeout") / 1000

    def send_receive(self, data):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.con_timeout)
            self.socket.sendto(data, (self.host, self.port))
            data = self.socket.recv(2048)
            self.socket.close()
            self.socket = None
            return data
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return None


class HttpClient:

    def __init__(self):
        pass

    def send_receive(self, uri, path):
        try:
            return urllib.request.urlopen(uri + path).read()
        except (urllib.error.URLError, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return None
