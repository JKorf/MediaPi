import socket
import urllib.request

from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from Shared.Logger import Logger
from Shared.Util import headers


class TcpClient:

    def __init__(self, host, port, connection_timeout):
        self.host = host
        self.port = port
        if self.port == 0:
            self.port = 6881
        self.socket = None
        self.connection_timeout = connection_timeout

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.connection_timeout)
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

    def receive_available(self, max_bytes):
        try:
            return bytes(self.socket.recv(max_bytes))
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
            self.socket = None


class UdpClient:

    def __init__(self, host, port, connection_timeout):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(connection_timeout)

    def send(self, data):
        try:
            self.socket.sendto(data, (self.host, self.port))
            return True
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return False

    def receive(self):
        try:
            data = self.socket.recv(2048)
            return data
        except (socket.timeout, socket.gaierror, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            return None


class RequestFactory:

    @staticmethod
    async def make_request_async(url, method='GET', body=None, heads=None, request_timeout=10, connect_timeout=10, useragent=None):
        try:
            com = dict(headers)
            if heads:
                com.update(heads)
            if method == 'POST' and not body:
                body = b""

            async_http_client = AsyncHTTPClient()
            http_request = HTTPRequest(url, method=method, headers=com, body=body, request_timeout=request_timeout, connect_timeout=connect_timeout, user_agent=useragent)
            http_response = await async_http_client.fetch(http_request)
            return http_response.body
        except Exception as e:
            Logger.write(2, "Error requesting url " + url + ": " + str(e))
            return None

    @staticmethod
    def make_request(path, method="GET", useragent=None):
        try:
            body = None
            if method == 'POST':
                body = b""
            heads = headers
            if useragent:
                heads = {
                    'User-Agent': useragent
                }

            request = urllib.request.Request(path, body, heads, method=method)
            return urllib.request.urlopen(request).read()
        except Exception as e:
            Logger.write(2, "Error requesting url " + path + ": " + str(e))
            return None
