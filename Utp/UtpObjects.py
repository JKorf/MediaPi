from enum import Enum

from TorrentSrc.Util.Network import write_int_as_byte, write_ushort, write_uint, read_byte_as_int, read_uinteger, \
    read_ushort


class MessageType(Enum):
    ST_DATA = 0
    ST_FIN = 1
    ST_STATE = 2
    ST_RESET = 3
    ST_SYN = 4


class ConnectionState(Enum):
    CS_INITIAL = 1
    CS_SYN_SENT = 2
    CS_SYN_RECV = 3
    CS_CONNECTED = 4
    CS_DISCONNECTED = 5


class UtpPacket:

    def __init__(self, message_type, version, extensions, connection_id, timestamp, timestamp_dif, wnd_size, seq_nr, ack_nr, data=None):
        self.message_type = message_type
        self.version = version
        self.extensions = extensions
        self.connection_id = connection_id
        self.timestamp = timestamp
        self.timestamp_dif = timestamp_dif
        self.wnd_size = wnd_size
        self.seq_nr = seq_nr
        self.ack_nr = ack_nr
        self.data = data

        self.length = 20
        if self.data is not None:
            self.length += len(self.data)

    def to_bytes(self):
        result = bytearray(20)
        offset = 0
        offset = write_int_as_byte(result, self.message_type.value << 4 | self.version, offset)
        offset = write_int_as_byte(result, 0, offset) # TODO Actual extension
        offset = write_ushort(result, self.connection_id, offset)
        offset = write_uint(result, self.timestamp, offset)
        offset = write_uint(result, self.timestamp_dif, offset)
        offset = write_uint(result, self.wnd_size, offset)
        offset = write_ushort(result, self.seq_nr, offset)
        offset = write_ushort(result, self.ack_nr, offset)
        if self.data is not None:
            result += self.data
        return result

    def __str__(self):
        str_rep = "Type: " + str(self.message_type) + ", Version: " + str(self.version) + ", Ext: " + str(self.extensions)\
             + ", ConnectionId: " + str(self.connection_id) + ", Timestamp: " + str(self.timestamp) + ", Timestamp dif"\
             + ": " + str(self.timestamp_dif) + ", WindowSize: " + str(self.wnd_size) + ", SeqNr: " + str(self.seq_nr)\
             + ", AckNr: " + str(self.ack_nr)
        if self.data is not None:
            str_rep += ", DataLength: " + str(len(self.data))
        return str_rep

    @classmethod
    def from_bytes(cls, data):
        offset = 0
        offset, type_version = read_byte_as_int(data, offset)
        offset, extensions = read_byte_as_int(data, offset)
        offset, con_id = read_ushort(data, offset)
        offset, timestamp = read_uinteger(data, offset)
        offset, timestamp_dif = read_uinteger(data, offset)
        offset, wnd_size = read_uinteger(data, offset)
        offset, seq_nr = read_ushort(data, offset)
        offset, ack_nr = read_ushort(data, offset)

        inst = cls(MessageType(type_version >> 4), type_version & 0x0f, extensions, con_id, timestamp, timestamp_dif, wnd_size, seq_nr, ack_nr)
        if len(data) > offset:
            inst.data = data[offset:]
        return inst
