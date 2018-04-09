import os
import random
import socket
import time

from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Threading import CustomThread

from Shared.Events import EventType

from Shared.Events import EventManager


class StreamListener:

    wait_for_data = 0.150

    mime_mapping = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mkv": "video/mp4"
    }

    def __init__(self, torrent, port):
        self.torrent = torrent
        self.port = port
        self.thread = None
        self.request_thread = None
        self.chunk_length = Settings.get_int("max_chunk_size")
        self.server = StreamServer(port, self.handle_request)
        self.running = False
        self.last_request_id = 0
        self.request_count = 0
        self.bytes_send = 0
        self.seeking = False

    def start_listening(self):
        self.thread = CustomThread(self.server.start, "Stream listener")
        self.running = True
        self.thread.start()

    def handle_request(self, socket):
        self.last_request_id = random.randint(0, 99999999)
        self.request_count += 1
        Logger.write(2, "New request, now " + str(self.request_count) + " connections")

        try:
            total_message = b''
            while not total_message.endswith(b'\r\n\r\n'):
                rec = socket.recv(1024)
                if len(rec) == 0:
                    break
                total_message += rec
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            Logger.write(2, "Error reading http header")
            return

        if not total_message.endswith(b'\r\n\r\n'):
            Logger.write(2, "Invalid http header, closing. now " + str(self.request_count) + " connections")
            return

        header = HttpHeader.from_string(total_message)

        while not self.torrent or not self.torrent.media_file:
            if not self.running:
                self.request_count -= 1
                Logger.write(2, "Stopping connection, now " + str(self.request_count) + " connections")
                return
            time.sleep(0.5)

        if header.range_end == 0 or header.range_end == -1:
            header.range_end = self.torrent.media_file.length - 1
        range_start = 0
        if header.range:
            range_start = header.range_start

        EventManager.throw_event(EventType.NewRequest, [range_start])
        if header.range is None:
            Logger.write(2, 'request without range')
            self.write_header(socket, "200 OK", 0, header.range_end)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, self.last_request_id)
        else:
            Logger.write(2, 'request with range')
            self.write_header(socket, "206 Partial Content", header.range_start, header.range_end)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, self.last_request_id)

        self.request_count -= 1
        Logger.write(2, "Shutting down request, now " + str(self.request_count) + " connections")
        socket.close()

    def write_header(self, socket, status, start, end):
        if end == -1:
            end = self.torrent.media_file.length - 1

        response_header = HttpHeader()
        Logger.write(2, "stream requested: " + str(start) + "-" + str(end))

        response_header.status_code = status
        response_header.content_length = end - start + 1
        response_header.set_range(start, end, self.torrent.media_file.length)
        filename, file_extension = os.path.splitext(self.torrent.media_file.path)
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

    def write_data(self, socket, requested_byte, length, request_id):
        written = 0
        Logger.write(2, "Write data: " + str(requested_byte) + ", length " + str(length))

        while written < length:
            part_length = min(length - written, self.chunk_length)
            if request_id != self.last_request_id:
                Logger.write(2, "Got data for connection which was not the last one 1 " + str(requested_byte) + ", " + str(length))
                return

            data = self.torrent.get_data_bytes_for_stream(requested_byte + written, part_length)
            if not self.running:
                Logger.write(2, "Canceling retrieved data because we are no longer running")
                return

            if request_id != self.last_request_id:
                Logger.write(2, "Got data for connection which was not the last one 2 " + str(requested_byte) + ", " + str(length))
                return

            if data is None:
                time.sleep(self.wait_for_data)
                continue

            Logger.write(2, 'Data retrieved: ' + str(requested_byte + written) + " - " + str(requested_byte + written + part_length))

            try:
                socket.sendall(data)
                written += len(data)
                self.bytes_send += len(data)
            except (ConnectionAbortedError, ConnectionResetError) as e:
                Logger.write(2, "Connection closed 3: " + str(e))
                return

    def stop(self):
        self.running = False
        if self.server is not None:
            self.server.close()


class StreamServer:

    def __init__(self, port, client_thread):
        self.port = port
        self.soc = None
        self.running = False
        self.client_thread = client_thread

    def start(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

        try:
            self.soc.bind(("127.0.0.1", self.port))
            Logger.write(2, "StreamServer running on port " + str(self.port))
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


class HttpHeader:

    def __init__(self):
        self.host = None
        self.range = None
        self.range_start = 0
        self.range_end = 0
        self.range_total = 0

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
