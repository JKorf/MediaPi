import os
import socket
import sys
import urllib.parse
from threading import Lock

import time

import select

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import current_time


class StreamListener:

    wait_for_data = 0.1

    mime_mapping = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mkv": "video/mp4",
        ".srt": "json"
    }

    @property
    def stream_speed(self):
        return max([x.stream_speed for x in self.sockets_writing_data], default=0)

    def __init__(self, name, port, arg=None):

        self.name = name
        self.torrent = arg

        self.port = port
        self.thread = None
        self.chunk_length = Settings.get_int("max_chunk_size")
        self.server = StreamServer(self.name, port, self.handle_request)

        self.sockets_writing_data = []

        self.running = False
        self.bytes_send = 0
        self.id = 0

    def start_listening(self):
        self.thread = CustomThread(self.server.start, "Listener: " + self.name)
        self.running = True
        self.thread.start()

    def handle_request(self, socket):
        Logger().write(LogVerbosity.Info, self.name + " new request")

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
            Logger().write(LogVerbosity.Info, self.name + " streamListener received unknown request: " + header.path)
            socket.close()

    def read_headers(self, socket):
        try:
            total_message = b''
            while not total_message.endswith(b'\r\n\r\n'):
                rec = socket.recv(1024)
                if len(rec) == 0:
                    break
                total_message += rec
                time.sleep(0)
        except (socket.timeout, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
            socket.close()
            Logger().write(LogVerbosity.Info, self.name + " error reading http header")
            return

        if not total_message.endswith(b'\r\n\r\n'):
            socket.close()
            Logger().write(LogVerbosity.Info, self.name + " invalid http header, closing")
            return
        return total_message

    def handle_file_request(self, socket, header):
        file_path = header.path[6:]
        if sys.platform == "linux" or sys.platform == "linux2":
            file_path = "/" + file_path

        Logger().write(LogVerbosity.Debug, self.name + " file request for " + file_path)

        if not os.path.exists(file_path):
            file_path = urllib.parse.unquote_plus(file_path)
            if not os.path.exists(file_path):
                Logger().write(LogVerbosity.Info, self.name + " file not found: " + file_path)
                self.write_header(socket, "404 Not Found")
                socket.close()
                return

        read_file = ReadFile(file_path)
        read_file.open()

        if header.range_end == 0 or header.range_end == -1:
            header.range_end = read_file.size - 1

        if header.range is None:
            Logger().write(LogVerbosity.Debug, self.name + ' request without range')
            self.write_header_with_content(socket, "200 OK", 0, header.range_end, read_file.size, file_path)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, read_file.get_bytes)
        else:
            Logger().write(LogVerbosity.Debug, self.name + ' request with range')
            self.write_header_with_content(socket, "206 Partial Content", header.range_start, header.range_end, read_file.size, file_path)
            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1, read_file.get_bytes)
        read_file.close()

    def handle_torrent_request(self, socket, header):
        if not self.torrent or not self.running:
            socket.close()
            Logger().write(LogVerbosity.Debug, self.name + " stopping connection because there is no more torrent")
            return

        if header.range_end == 0 or header.range_end == -1:
            header.range_end = self.torrent.media_file.length - 1

        if header.range:
            range_start = header.range_start
            if range_start == self.torrent.media_file.length:
                Logger().write(LogVerbosity.Debug, "Request for content length 0, cant process")
                self.write_header(socket, "416 Requested range not satisfiable")
                socket.close()
                return

        if header.range is None:
            Logger().write(LogVerbosity.Debug, self.name + ' request without range')
            success = self.write_header_with_content(socket, "200 OK", 0, header.range_end, self.torrent.media_file.length,
                              self.torrent.media_file.path)

            if not success:
                return

            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1,
                            self.torrent.get_data_bytes_for_stream)
        else:
            Logger().write(LogVerbosity.Debug, self.name + ' request with range')
            success = self.write_header_with_content(socket, "206 Partial Content", header.range_start, header.range_end,
                              self.torrent.media_file.length, self.torrent.media_file.path)

            if not success:
                return

            self.write_data(socket, header.range_start, header.range_end - header.range_start + 1,
                            self.torrent.get_data_bytes_for_stream)

    def write_header(self, socket, status):
        response_header = HttpHeader()
        response_header.status_code = status

        Logger().write(LogVerbosity.Info, self.name + " return header: " + response_header.to_string())

        try:
            socket.send(response_header.to_string().encode())
            return True
        except (ConnectionAbortedError, ConnectionResetError, OSError):
            Logger().write(LogVerbosity.Info, "Connection closed 2 during sending of response header")
            socket.close()
            return False

    def write_header_with_content(self, socket, status, start, end, length, path):
        response_header = HttpHeader()
        Logger().write(LogVerbosity.Debug, self.name + " stream requested: " + str(start) + "-" + str(end))

        response_header.status_code = status
        response_header.content_length = end - start + 1
        response_header.set_range(start, end, length)
        filename, file_extension = os.path.splitext(path.lower())
        if file_extension not in StreamListener.mime_mapping:
            Logger().write(LogVerbosity.Info, self.name + " unknown video type: " + str(file_extension) + ", defaulting to mp4")
            response_header.mime_type = StreamListener.mime_mapping[".mp4"]
        else:
            response_header.mime_type = StreamListener.mime_mapping[file_extension]

        Logger().write(LogVerbosity.Info, self.name + " return header: " + response_header.to_string())

        try:
            socket.send(response_header.to_string().encode())
            return True
        except (ConnectionAbortedError, ConnectionResetError, OSError):
            Logger().write(LogVerbosity.Info, "Connection closed 2 during sending of response header")
            socket.close()
            return False

    def write_data(self, socket, requested_byte, length, data_delegate):
        written = 0
        Logger().write(LogVerbosity.Info, self.name + " write data: " + str(requested_byte) + ", length " + str(length))
        id = self.id
        self.id += 1
        data_writer = SocketWritingData(id, socket, requested_byte, requested_byte + length, current_time())
        self.sockets_writing_data.append(data_writer)
        if len(self.sockets_writing_data) > 1:
            Logger().write(LogVerbosity.Debug, "Multiple data writers:")
            for writer in self.sockets_writing_data:
                Logger().write(LogVerbosity.Debug, "    " + str(writer))

        while written < length:
            part_length = min(length - written, self.chunk_length)
            if not self.running:
                Logger().write(LogVerbosity.Debug, self.name + ' writer ' + str(data_writer.id) + " canceling retrieved data because we are no longer running 1")
                socket.close()
                self.sockets_writing_data.remove(data_writer)
                return

            if not self.wait_writable(socket):
                Logger().write(LogVerbosity.Debug, self.name + ' writer ' + str(data_writer.id) + " closed")
                self.sockets_writing_data.remove(data_writer)
                return

            data = data_delegate(requested_byte + written, part_length)
            if not self.running:
                Logger().write(LogVerbosity.Debug, self.name + ' writer ' + str(data_writer.id) + " canceling retrieved data because we are no longer running 2")
                socket.close()
                self.sockets_writing_data.remove(data_writer)
                return

            if data is None:
                time.sleep(self.wait_for_data)
                continue

            Logger().write(LogVerbosity.Info, self.name + ' writer ' + str(data_writer.id) + ' data retrieved: ' + str(requested_byte + written) + " - " + str(requested_byte + written + part_length))
            send = 0
            try:
                while send < len(data):
                    this_send = data[send: send + 50000]
                    data_length = len(this_send)
                    socket.sendall(this_send)
                    written += data_length
                    send += data_length
                    self.bytes_send += data_length
                    data_writer.streamed += data_length
                    Logger().write(LogVerbosity.All, self.name + ' writer ' + str(data_writer.id) + " send " + str(data_length) + " bytes")
                    time.sleep(0)  # give other threads some time
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                Logger().write(LogVerbosity.Info, self.name + " writer " + str(data_writer.id) + " connection closed during sending of data: " + str(e))
                socket.close()
                self.sockets_writing_data.remove(data_writer)
                return

        Logger().write(LogVerbosity.Info, "Completed request: " + str(data_writer))
        socket.close()
        self.sockets_writing_data.remove(data_writer)

    def wait_writable(self, socket):
        while True:
            if not self.running:
                return False

            # check if socket is still open
            readable, writeable, exceptional = select.select([socket], [socket], [socket], 0)
            if len(readable) == 1:
                read = socket.recv(1)
                if len(read) == 0:
                    Logger().write(LogVerbosity.Info, self.name + " socket no longer open 3")
                    socket.close()
                    return False
                else:
                    Logger().write(LogVerbosity.Info, self.name + " recv received data??")

            if len(writeable) == 0:
                # not currently writeable, wait for it to become available again
                time.sleep(0.1)
                continue

            return True

    def stop(self):
        self.running = False
        self.torrent = None
        if self.server is not None:
            self.server.close()
        Logger().write(LogVerbosity.Info, self.name + " stopped")


class StreamServer:

    def __init__(self, name, port, client_thread):
        self.port = port
        self.name = name
        self.soc = None
        self.running = False
        self.client_thread = client_thread

    def start(self):
        Logger().write(LogVerbosity.Debug, self.name + " starting listener on port " + str(self.port))
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

        try:
            self.soc.bind(("", self.port))
            Logger().write(LogVerbosity.Info, "StreamServer "+self.name+" listening on port " + str(self.port))
        except (socket.error, OSError) as e:
            Logger().write(LogVerbosity.Info, "Couldn't start StreamServer " + self.name + ": " + str(e))
            return

        self.soc.listen(10)

        try:
            while True:
                conn, addr = self.soc.accept()
                if not self.running:
                    break
                ip, port = str(addr[0]), str(addr[1])
                Logger().write(LogVerbosity.Debug, 'New connection from ' + ip + ':' + port)
                thread = CustomThread(self.client_thread, "Stream thread", [conn])
                thread.start()
        except Exception as e:
            Logger().write(LogVerbosity.Important, "Unexpected error in StreamServer " + self.name + ": " + str(e))

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
        with self.read_lock:
            if self.location != start:
                Logger().write(LogVerbosity.Info, "Seeking file to " + str(start))
                self.file.seek(start)
            data = self.file.read(length)
            self.location = start + len(data)
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
        header = header.decode('utf8')
        Logger().write(LogVerbosity.Info, "Received header: " + header)
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
        if self.mime_type:
            result += "Content-Type: " + self.mime_type + "\r\n"
        if self.content_length:
            result += "Accept-Ranges: bytes" + "\r\n"
            result += "Content-Length: " + str(self.content_length) + "\r\n"
            result += "Content-Range: " + self.range + "\r\n" + "\r\n"
        return result


class SocketWritingData:

    @property
    def stream_speed(self):
        return self.streamed / ((current_time() - self.connect_time) / 1000)

    def __init__(self, id, socket, range_start, range_end, connect_time):
        self.id = id
        self.socket = socket
        self.range_start = range_start
        self.range_end = range_end
        self.connect_time = connect_time
        self.streamed = 0

    def __str__(self):
        return "Id: "+str(self.id)+", Range: " + str(self.range_start) + "-" + str(self.range_end) + " connected at " + str(self.connect_time) + ", streamed: " +str(self.streamed)

