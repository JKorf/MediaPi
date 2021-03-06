from MediaPlayer.Util.Network import read_integer, read_long, write_long, write_int, write_bytes, write_uint, \
    write_ushort
from MediaPlayer.Util.Util import check_bytes_length, check_minimal_bytes_length, uri_from_bytes
from Shared.Logger import Logger, LogVerbosity


class TrackerConnectionMessage:

    def __init__(self, connection_id, transaction_id, action):
        self.connection_id = connection_id
        self.transaction_id = transaction_id
        self.action = action

    @classmethod
    def for_send(cls, connection_id, transaction_id):
        return cls(connection_id, transaction_id, 0)

    @classmethod
    def for_receive(cls, data):
        if not check_bytes_length(data, 16):
            return None

        offset = 0
        offset, action = read_integer(data, offset)
        offset, transaction_id = read_integer(data, offset)
        offset, connection_id = read_long(data, offset)

        return cls(connection_id, transaction_id, action)

    def as_bytes(self):
        offset = 0
        buffer = bytearray(16)
        offset = write_long(buffer, self.connection_id, offset)
        offset = write_int(buffer, self.action, offset)
        write_int(buffer, self.transaction_id, offset)

        return buffer


class TrackerResponseMessage:

    def __init__(self):
        self.peers = None
        self.error = None
        self.message_type = 0
        self.transaction_id = 0
        self.interval = 0
        self.leechers = 0
        self.seeders = 0

    @staticmethod
    def from_bytes(data):
        if not check_minimal_bytes_length(data, 8):
            return None

        msg = TrackerResponseMessage()

        offset = 0
        msg.peers = list()
        msg.error = None

        try:
            offset, msg.message_type = read_integer(data, offset)
            offset, msg.transaction_id = read_integer(data, offset)
            if msg.message_type == 3:
                msg.error = str(data[offset: len(data)])
                Logger().write(LogVerbosity.Important, "Tracker error message: " + msg.error)
            else:
                offset, msg.interval = read_integer(data, offset)
                offset, msg.leechers = read_integer(data, offset)
                offset, msg.seeders = read_integer(data, offset)

                bytes_left = len(data) - offset
                total_peers = int(bytes_left / 6)
                for index in range(total_peers):
                    msg.peers.append(uri_from_bytes(data[offset:offset + 6]))
                    offset += 6
        except Exception as e:
            Logger().write(LogVerbosity.Important, "Error in tacker message: " +str(e) + ". Message: " + str(data))
            return None

        return msg


class TrackerAnnounceMessage:

    def __init__(self, connection_id, transaction_id, info_hash, message_event, downloaded, left, uploaded, num_want, port):
        self.connection_id = connection_id
        self.transaction_id = transaction_id
        self.info_hash = info_hash
        self.message_type = 1
        self.message_event = message_event
        self.peer_id = b'-JK0001-100000100000'
        self.downloaded = downloaded
        self.left = left
        self.uploaded = uploaded
        self.ip = 0
        self.key = 0
        self.num_want = num_want
        self.port = port
        self.Extensions = 0

    @classmethod
    def for_http(cls, info_hash, message_event, downloaded, left, uploaded, num_want):
        return cls(0, 0, info_hash, message_event, downloaded, left, uploaded, num_want, 0)

    @classmethod
    def for_udp(cls, connection_id, transaction_id, info_hash, message_event, downloaded, left, uploaded, num_want, port):
        return cls(connection_id, transaction_id, info_hash, message_event, downloaded, left, uploaded, num_want, port)

    def as_bytes(self):
        offset = 0
        buffer = bytearray(98)
        offset = write_long(buffer, self.connection_id, offset)
        offset = write_int(buffer, self.message_type, offset)
        offset = write_int(buffer, self.transaction_id, offset)
        offset = write_bytes(buffer, self.info_hash.sha1_hashed_bytes, offset)
        buffer[offset: offset + 20] = self.peer_id
        offset += 20
        offset = write_long(buffer, self.downloaded, offset)
        offset = write_long(buffer, self.left, offset)
        offset = write_long(buffer, self.uploaded, offset)
        offset = write_int(buffer, self.message_event, offset)
        offset = write_uint(buffer, self.ip, offset)
        offset = write_uint(buffer, self.key, offset)
        offset = write_int(buffer, self.num_want, offset)
        write_ushort(buffer, self.port, offset)

        return buffer

    def as_param_string(self):
        result = "?"
        result += "info_hash=" + self.info_hash.url_encoded
        result += "&peer_id=" + str(self.peer_id)
        result += "&port=" + str(self.port)
        result += "&uploaded=" + str(self.uploaded)
        result += "&downloaded=" + str(self.downloaded)
        result += "&left=" + str(self.left)
        result += "&event=" + str(self.message_event)
        return result
