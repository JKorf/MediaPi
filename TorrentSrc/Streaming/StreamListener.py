import os
import random
import sys
import urllib.parse
import socket
import time
from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Threading import CustomThread

from Shared.Events import EventType

from Shared.Events import EventManager


class StreamListener:

    wait_for_data = 0.5

    mime_mapping = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mkv": "video/mp4"
    }

    def __init__(self, name, port, arg=None):

        self.name = name
        self.torrent = arg

        self.port = port
        self.thread = None
        self.request_thread = None
        self.chunk_length = Settings.get_int("max_chunk_size")
        self.server = StreamServer(self.name, port, self.handle_request)
        self.requests = []
        self.running = False
        self.bytes_send = 0
        self.id = 0
        EventManager.register_event(EventType.Log, self.log_requests)
        EventManager.register_event(EventType.Seek, self.seek)

    def seek(self, pos):
        for (id, socket, status) in self.requests:
            socket.close()

    def log_requests(self):
        Logger.write(2, "REQUESTS:")
        for client in self.requests:
            Logger.write(2, str(client[0]) + ": " + client[2])

    def start_listening(self):
        self.thread = CustomThread(self.server.start, "Stream listener: " + self.name)
        self.running = True
        self.thread.start()

    def handle_request(self, socket):
        self.add_socket(socket, "")
        Logger.write(2, "New request, now " + str(len(self.requests)))

        # Read headers
        total_message = self.read_headers(socket)
        if total_message is None:
            return

        header = HttpHeader.from_string(total_message)
        if header.path == "/torrent":
            # Handle torrent stream request
            self.handle_torrent_request(socket, header)
        elif header.path.startswith("/file"):
            # Handle file stream request
            self.handle_file_request(socket, header)
        else:
            # Unknown request
            Logger.write(2, "Received unknown request: " + header.path)

        # Request completed, close
        if self.in_requests(socket):
            socket.close()
            self.remove_socket(socket)
            Logger.write(2, "Request finished, now " + str(len(self.requests)))

    def read_headers(self, socket):
        try:
            total_message = b''
            while not total_message.endswith(b'\r\n\r\n'):
                rec = socket.recv(1024)
                if len(rec) == 0:
                    break
                total_message += rec
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            socket.close()
            self.remove_socket(socket)
            Logger.write(2, "Error reading http header, now " + str(len(self.requests)))
            return

        if not total_message.endswith(b'\r\n\r\n'):
            socket.close()
            self.remove_socket(socket)
            Logger.write(2, "Invalid http header, closing, now " + str(len(self.requests)))
            return
        return total_message

    def handle_file_request(self, socket, header):
        file_path = header.path[6:]
        if sys.platform == "linux" or sys.platform == "linux2":
            file_path = "/" + file_path

        if not os.path.exists(file_path):
            file_path = urllib.parse.unquote_plus(file_path)
            if not os.path.exists(file_path):
                Logger.write(2, "File not found: " + file_path)
                socket.close()
                self.remove_socket(socket)
                return

        read_file = ReadFile(file_path)
        read_file.open()

        if header.range_end == 0 or header.range_end == -1:
            header.range_end = read_file.size - 1

        if header.range is None:
            Logger.write(2, 'request without range')
            self.update_socket(socket, "Without range: 0 - " + str(header.range_end))
            self.write_header(socket, "200 OK", 0, header.range_end, read_file.size, file_path)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, read_file.get_bytes)
        else:
            Logger.write(2, 'request with range')
            self.update_socket(socket, "With range: " + str(header.range_start) + " - " + str(header.range_end))
            self.write_header(socket, "206 Partial Content", header.range_start, header.range_end, read_file.size, file_path)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, read_file.get_bytes)
        read_file.close()

    def handle_torrent_request(self, socket, header):
        while not self.torrent or not self.torrent.media_file:
            if not self.running:
                socket.close()
                self.remove_socket(socket)
                Logger.write(2, "Stopping connection because there is no more torrent, now " + str(len(self.requests)))
                return
            time.sleep(0.5)

        if header.range_end == 0 or header.range_end == -1:
            header.range_end = self.torrent.media_file.length - 1
        range_start = 0
        if header.range:
            range_start = header.range_start

        if self.in_requests(socket):
            EventManager.throw_event(EventType.NewRequest, [range_start])
            if header.range is None:
                Logger.write(2, 'request without range')
                self.update_socket(socket, "Without range: 0 - " + str(header.range_end))
                self.write_header(socket, "200 OK", 0, header.range_end, self.torrent.media_file.length,
                                  self.torrent.media_file.path)
                self.write_data(socket, header.range_start, header.range_end - header.range_start + 1,
                                self.torrent.get_data_bytes_for_stream)
            else:
                Logger.write(2, 'request with range')
                self.update_socket(socket, "With range: " + str(header.range_start) + " - " + str(header.range_end))
                self.write_header(socket, "206 Partial Content", header.range_start, header.range_end,
                                  self.torrent.media_file.length, self.torrent.media_file.path)
                self.write_data(socket, header.range_start, header.range_end - header.range_start + 1,
                                self.torrent.get_data_bytes_for_stream)

    def write_header(self, socket, status, start, end, length, path):
        response_header = HttpHeader()
        Logger.write(2, "stream requested: " + str(start) + "-" + str(end))

        response_header.status_code = status
        response_header.content_length = end - start + 1
        response_header.set_range(start, end, length)
        filename, file_extension = os.path.splitext(path)
        if file_extension not in StreamListener.mime_mapping:
            Logger.write(2, "Unknown video type: " + str(file_extension) + ", defaulting to mp4")
            response_header.mime_type = StreamListener.mime_mapping[".mp4"]
        else:
            response_header.mime_type = StreamListener.mime_mapping[file_extension]

        Logger.write(2, "return header: " + response_header.to_string())

        try:
            socket.send(response_header.to_string().encode())
        except (ConnectionAbortedError, ConnectionResetError):
            Logger.write(2, "Connection closed 2")
            return

    def write_data(self, socket, requested_byte, length, data_delegate):
        written = 0
        Logger.write(2, "Write data: " + str(requested_byte) + ", length " + str(length))

        while written < length:
            part_length = min(length - written, self.chunk_length)
            if not self.in_requests(socket):
                Logger.write(2, "Socket no longer open 1: " + str(requested_byte) + ", " + str(length))
                return

            data = data_delegate(requested_byte + written, part_length)
            if not self.running:
                Logger.write(2, "Canceling retrieved data because we are no longer running")
                return

            if not self.in_requests(socket):
                Logger.write(2, "Socket no longer open 2: " + str(requested_byte) + ", " + str(length))
                return

            if data is None:
                try:
                    socket.settimeout(self.wait_for_data)
                    socket.recv(1)
                except OSError as e:
                    if e.args[0] != 'timed out':
                        Logger.write(2, "Socket no longer open 3: " + str(type(e)) + "" + str(requested_byte) + ", " + str(length))
                        return
                continue

            socket.settimeout(None)
            Logger.write(2, 'Data retrieved: ' + str(requested_byte + written) + " - " + str(requested_byte + written + part_length))
            send = 0
            try:
                while send < len(data):
                    this_send = data[send: send + 50000]
                    socket.sendall(this_send)
                    written += len(this_send)
                    send += len(this_send)
                    self.bytes_send += len(this_send)
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                Logger.write(2, "Connection closed 3: " + str(e))
                return

    def add_socket(self, socket, status):
        self.requests.append((self.id, socket, status))
        Logger.write(2, "Added request with id " + str(self.id))
        self.id += 1

    def update_socket(self, socket, status):
        tup = [x for x in self.requests if x[1] == socket][0]
        self.requests.remove(tup)
        self.requests.append((tup[0], tup[1], status))

    def in_requests(self, socket):
        return len([x for x in self.requests if x[1] == socket])

    def remove_socket(self, socket):
        tup = [x for x in self.requests if x[1] == socket][0]
        self.requests.remove(tup)
        Logger.write(2, "Removed client with id " + str(tup[0]))

    def stop(self):
        self.running = False
        if self.server is not None:
            self.server.close()


class StreamServer:

    def __init__(self, name, port, client_thread):
        self.port = port
        self.name = name
        self.soc = None
        self.running = False
        self.client_thread = client_thread

    def start(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

        try:
            self.soc.bind(("", self.port))
            Logger.write(2, "StreamServer "+self.name+" running on port " + str(self.port))
        except (socket.error, OSError):
            pass

        self.soc.listen(10)

        try:
            while True:
                conn, addr = self.soc.accept()
                if not self.running:
                    break
                ip, port = str(addr[0]), str(addr[1])
                Logger.write(1, 'New connection from ' + ip + ':' + port)
                thread = CustomThread(self.client_thread, "Stream thread", [conn])
                thread.start()
        except OSError:
            pass
        self.soc.close()

    def close(self):
        self.running = False
        if self.soc is not None:
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("127.0.0.1", self.port))
            except ConnectionRefusedError:
                pass


class ReadFile:

    def __init__(self, path):
        self.path = path
        self.size = os.path.getsize(path)
        self.read_lock = Lock()
        self.location = 0
        self.file = None

    def open(self):
        self.file = open(self.path, 'rb')
        self.location = 0

    def get_bytes(self, start, length):
        self.read_lock.acquire()
        if self.location != start:
            Logger.write(2, "Seeking file to " + str(start))
            self.file.seek(start)
        data = self.file.read(length)
        self.location = start + len(data)
        self.read_lock.release()
        return data

    def close(self):
        self.file.close()


class HttpHeader:

    def __init__(self):
        self.host = None
        self.range = None
        self.range_start = 0
        self.range_end = 0
        self.range_total = 0
        self.path = None

        self.content_length = 0
        self.mime_type = None
        self.accept_ranges = None
        self.connection = None
        self.status_code = None

    @classmethod
    def from_string(cls, header):
        header = header.decode('ascii')
        Logger.write(2, "Received: " + header)
        result = cls()
        split = header.splitlines(False)
        request = split[0].split(" ")
        result.path = request[1]
        for head in split:
            keyvalue = head.split(': ')
            if len(keyvalue) != 2:
                continue

            if keyvalue[0] == "Host":
                result.host = keyvalue[1]
            if keyvalue[0] == "Range":
                result.range = keyvalue[1]
                type_bytes = result.range.split("=")
                start_end = type_bytes[1].split("-")
                result.range_start = int(start_end[0])
                if len(start_end) > 1 and start_end[1] is not "":
                    result.range_end = int(start_end[1])
                else:
                    result.range_end = -1

            if keyvalue[0] == "Content-Length":
                result.content_length = keyvalue[1]

        return result

    def set_range(self, start, end, total):
        self.range = "bytes " + str(start) + "-" + str(end) + "/" + str(total)

    def to_string(self):
        result = ""
        result += "HTTP/1.1 " + self.status_code + "\r\n"
        result += "Content-Type: " + self.mime_type + "\r\n"
        result += "Accept-Ranges: bytes" + "\r\n"
        result += "Content-Length: " + str(self.content_length) + "\r\n"
        result += "Content-Range: " + self.range + "\r\n" + "\r\n"
        return result
