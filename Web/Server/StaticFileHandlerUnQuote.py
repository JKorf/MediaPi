import os

import datetime
import traceback
import urllib.parse
from tornado.web import RequestHandler, HTTPError
from tornado import gen

from Shared.Logger import Logger


class StaticFileHandlerUnQuote(RequestHandler):
    mime_mapping = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mkv": "video/mp4"
    }

    def initialize(self, path, default_filename=None):
        self.root = os.path.abspath(path)
        self.default_filename = default_filename

    def head(self, path):
        self.get(path, include_body=False)

    @gen.coroutine
    def get(self, path, include_body=True):
        try:
            Logger.write(2, "Request for path: "+path)

            if os.path.sep != "/":
                path = path.replace("/", os.path.sep)
            abspath = os.path.abspath(os.path.join(self.root, path))
            # os.path.abspath strips a trailing /
            # it needs to be temporarily added back for requests to root/
            if os.path.isdir(abspath) and self.default_filename is not None:
                # need to look at the request.path here for when path is empty
                # but there is some prefix to the path that was already
                # trimmed by the routing
                if not self.request.path.endswith("/"):
                    self.redirect(self.request.path + "/")
                    return
                abspath = os.path.join(abspath, self.default_filename)
            if not os.path.exists(abspath):
                Logger.write(2, abspath)
                abspath = urllib.parse.unquote_plus(abspath)
                Logger.write(2, abspath)

                if not os.path.exists(abspath):
                    raise HTTPError(404)
            if not os.path.isfile(abspath):
                raise HTTPError(403, "%s is not a file", path)

            self.request.connection.stream.socket.set_blocking(1)

            if not include_body:
                return

            file_size = os.path.getsize(abspath)
            headers = self.request.headers
            byte_range = headers.get_list("Range")
            if not byte_range:
                Logger.write(2, "Master file request without range")
                self.return_file_header("200 OK", 0, file_size - 1, file_size, abspath)
                self.return_file_range(abspath, 0, file_size - 1)
            else:
                key_value = byte_range[0].split('=')
                start_end = key_value[1].split('-')
                start = int(start_end[0])
                end = start_end[1]
                if not end:
                    end = file_size - 1
                end = int(end)

                Logger.write(2, "Master file request with range: " + str(start) + "-" + str(end))
                self.return_file_header("206 Partial Content", start, end, file_size, abspath)
                self.return_file_range(abspath, start, end)

        except Exception as e:
            Logger.write(3, "Exception in master request to "+path+": " + str(e))
            Logger.write(3, traceback.format_exc())

    @gen.coroutine
    def return_file_range(self, path, start, end):
        file = open(path, "rb")
        file.seek(start)
        each_read = 500000
        total_send = 0
        try:
            while total_send < end - start:
                read_data = file.read(each_read)
                self.request.connection.stream.socket.send(read_data)
                total_send += len(read_data)

        except Exception as e:
            Logger.write(3, "Exception in master write to " + path + ": " + str(e))
            Logger.write(3, traceback.format_exc())
        finally:
            Logger.write(2, "Written " + str(total_send) + "/" + str(end-start + 1) +" bytes, from " + str(start) + " to " + str(end))
            file.close()

    def return_file_header(self, status, start, end, length, path):
        response_header = HttpHeader()
        response_header.status_code = status
        response_header.content_length = end - start + 1
        response_header.set_range(start, end, length)
        filename, file_extension = os.path.splitext(path)
        if file_extension not in StaticFileHandlerUnQuote.mime_mapping:
            Logger.write(2, "Unknown video type: " + str(file_extension) + ", defaulting to mp4")
            response_header.mime_type = StaticFileHandlerUnQuote.mime_mapping[".mp4"]
        else:
            response_header.mime_type = StaticFileHandlerUnQuote.mime_mapping[file_extension]

        self.request.connection.stream.socket.send(response_header.to_string().encode())

    def set_extra_headers(self, path):
        """For subclass to add extra headers to the response"""
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
