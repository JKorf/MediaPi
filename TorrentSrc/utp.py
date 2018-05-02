from collections import namedtuple
from enum import Enum
from random import randrange
from time import time
import socket

from Shared.Logger import Logger
from Shared.Settings import Settings


class UtpClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.con_timeout = Settings.get_int("connection_timeout") / 1000
        self.utpPipe = MicroTransportProtocol(self.host, self.port)
        self.connected = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.con_timeout)
        return self.utpPipe.initiate_connection(self.socket)

    def send(self, data):
        return self.utpPipe.write(data)

    def receive_available(self, max):
        return self.utpPipe.receive_available(max)

    def receive(self, expected):
        return self.utpPipe.receive(expected)

    def disconnect(self):
        self.utpPipe.close()

# TODO
# Better/actual header parameters based on current state!
# Handle packet loss/resends
# Handle timeouts


class Type(Enum):
    ST_DATA = 0
    ST_FIN = 1
    ST_STATE = 2
    ST_RESET = 3
    ST_SYN = 4


def get_tms():
    return int(time() * 10000000) & 0xffffffff


def get_tms_diff():
    return (get_tms() + randrange(10000)) & 0xffffffff


class ConnectionState(Enum):
    CS_UNKNOWN = 1
    CS_SYN_SENT = 2
    CS_SYN_RECV = 3
    CS_CONNECTED = 4
    CS_DISCONNECTED = 5


class MicroTransportProtocol:
    def __init__(self, host, port):
        self.socket = None
        self.host = host
        self.port = port
        self.header_size = 20
        self.status = ConnectionState.CS_UNKNOWN
        self.seq_nr = 1
        self.ack_nr = 0
        self.conn_id_recv = randrange(0xffff)
        self.conn_id_send = self.conn_id_recv + 1
        self.extensions = [(2, bytes(8))]  # 2 -- EXTENSION_BITS

    def initiate_connection(self, socket):
        self.socket = socket

        packet = uTPPacket(
            type=Type.ST_SYN, ver=1,
            connection_id=self.conn_id_recv,
            timestamp=get_tms(),
            timestamp_diff=0,
            wnd_size=0,
            seq_nr=self.seq_nr,
            ack_nr=0,
            extensions=self.extensions,
            data=None
        )
        self.seq_nr += 1
        Logger.write(2, "Sending initial packet")
        try:
            self.socket.sendto(encode_packet(packet), (self.host, self.port))
            self.status = ConnectionState.CS_SYN_SENT
            received = self.socket.recv(self.header_size)
            self.__handle_package(received)
            self.socket.settimeout(None)
            return True
        except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError) as e:
            Logger.write(2, "Failed to connect: " + str(e))
            return False

    def write(self, data):
        packet = uTPPacket(
            type=Type.ST_DATA, ver=1,
            connection_id=self.conn_id_send,
            timestamp=get_tms(),
            timestamp_diff=get_tms_diff(),
            wnd_size=0xf000,
            seq_nr=self.seq_nr,
            ack_nr=self.ack_nr,
            extensions=None,
            data=data
        )
        self.seq_nr += 1
        Logger.write(2, "Sending data packet")
        try:
            send = self.socket.sendto(encode_packet(packet), (self.host, self.port))
            Logger.write(2, "Send " + str(send) + " bytes")
            return True
        except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError) as e:
            Logger.write(2, "Failed to send data packet: " + str(e))
            return False

    def receive(self, expected):
        Logger.write(2, "Going to try to read for " + str(expected) + " expected bytes")
        buffer = bytearray()
        total_received = 0
        while total_received < expected:
            try:
                act_data = True
                while act_data is True:
                    data = self.socket.recv((expected - total_received) + self.header_size)
                    act_data = self.__handle_package(data)
                    Logger.write(2, "Received 1 " + str(data))

            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError) as e:
                Logger.write(2, "Failed to received expected: " + str(e))
                return None

            if act_data is None or len(act_data) == 0:
                Logger.write(2, "Received nothing, closed: " + str(act_data))
                return None

            buffer.extend(act_data)
            total_received += len(act_data)
        return bytes(buffer)

    def receive_available(self, length):
        Logger.write(2, "Going to try to read for max " + str(length) + " bytes")
        try:
            act_data = True
            while act_data is True:
                data = self.socket.recv(length + self.header_size)
                act_data = self.__handle_package(data)
                Logger.write(2, "Received 2 " + str(data))
            return act_data
        except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError) as e:
            Logger.write(2, "Failed to receive available: " + str(e))
            return None

    def __handle_package(self, data):
        packet = decode_packet(data)
        self.ack_nr = packet.seq_nr
        Logger.write(2, "Received packet type " + str(packet.type) + " seq: " + str(packet.seq_nr))

        if packet.type == Type.ST_DATA:
            response = uTPPacket(
                type=Type.ST_STATE, ver=1,
                connection_id=self.conn_id_send,
                timestamp=get_tms(),
                timestamp_diff=get_tms_diff(),
                wnd_size=0xf000,
                seq_nr=self.seq_nr,
                ack_nr=self.ack_nr,
                extensions=None,
                data=None
            )
            self.socket.sendto(encode_packet(response), (self.host, self.port))

            if self.status == ConnectionState.CS_SYN_RECV:
                self.status = ConnectionState.CS_CONNECTED

            return packet.data
        elif packet.type == Type.ST_SYN:
            self.conn_id_recv = packet.connection_id + 1
            self.conn_id_send = packet.connection_id
            self.seq_nr = randrange(0xffff)
            self.ack_nr = packet.seq_nr
            self.status = ConnectionState.CS_SYN_RECV

            response = uTPPacket(
                type=Type.ST_STATE, ver=1,
                connection_id=self.conn_id_send,
                timestamp=get_tms(),
                timestamp_diff=get_tms_diff(),
                wnd_size=0xf000,
                seq_nr=self.seq_nr,
                ack_nr=self.ack_nr,
                extensions=self.extensions,
                data=None
            )
            self.seq_nr += 1
            self.socket.sendto(encode_packet(response), (self.host, self.port))
            return True
        elif packet.type == Type.ST_STATE:
            if self.status == ConnectionState.CS_SYN_SENT:
                self.status = ConnectionState.CS_CONNECTED
            return True
        elif packet.type == Type.ST_RESET:
            self.status = ConnectionState.CS_DISCONNECTED
            self.socket.close()
            return None
        elif packet.type == Type.ST_FIN:
            self.status = ConnectionState.CS_DISCONNECTED
            response = uTPPacket(
                type=Type.ST_FIN, ver=1,
                connection_id=self.conn_id_send,
                timestamp=get_tms(),
                timestamp_diff=get_tms_diff(),
                wnd_size=0xf000,
                seq_nr=self.seq_nr,
                ack_nr=self.ack_nr,
                extensions=None,
                data=None
            )
            self.socket.sendto(encode_packet(response), (self.host, self.port))
            self.socket.close()
            return None

    def close(self):
        if self.status == ConnectionState.CS_CONNECTED:
            self.status = ConnectionState.CS_DISCONNECTED
            response = uTPPacket(
                type=Type.ST_FIN, ver=1,
                connection_id=self.conn_id_send,
                timestamp=get_tms(),
                timestamp_diff=get_tms_diff(),
                wnd_size=0xf000,
                seq_nr=self.seq_nr,
                ack_nr=self.ack_nr,
                extensions=None,
                data=None
            )
            try:
                self.socket.sendto(encode_packet(response), (self.host, self.port))
            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError, OSError):
                pass
            self.socket.close()


uTPPacket = namedtuple("uTP_packet", [
    "type", "ver", "connection_id", "timestamp", "timestamp_diff", "wnd_size", "seq_nr", "ack_nr", "extensions", "data"
])


def decode_packet(data):
    def _split_bytes(data, lengths):
        idx = 0
        for l in lengths:
            result = data[idx:]
            yield result[:l] if l else result
            idx = idx + l if l else len(data)

    def _bytes_to_int(data):
        return int.from_bytes(data, "big")

    type_ver, next_ext_type, conn_id, tms, tms_diff, wnd, seq, ack, p_data = tuple(
        _split_bytes(data, (1, 1, 2, 4, 4, 4, 2, 2, 0))
    )

    p_type, p_ver = Type(type_ver[0] >> 4), type_ver[0] & 0x0f
    p_conn_id = _bytes_to_int(conn_id)
    p_timestamp = _bytes_to_int(tms)
    p_timestamp_diff = _bytes_to_int(tms_diff)
    p_wnd_size = _bytes_to_int(wnd)
    p_seq_nr = _bytes_to_int(seq)
    p_ack_nr = _bytes_to_int(ack)

    # Decode extensions
    p_extensions = []

    ext_type = next_ext_type[0]
    while ext_type:
        next_ext_type, ext_len, p_data = tuple(_split_bytes(p_data, (1, 1, 0)))
        ext_data, p_data = tuple(_split_bytes(p_data, (int.from_bytes(ext_len, "big"), 0)))
        p_extensions.append((ext_type, ext_data))
        ext_type = next_ext_type[0] if next_ext_type else 0

    return uTPPacket(
        p_type, p_ver, p_conn_id, p_timestamp, p_timestamp_diff, p_wnd_size, p_seq_nr, p_ack_nr, p_extensions, p_data
    )


def encode_packet(packet):
    def _int_to_bytes(data, bytes_len):
        return data.to_bytes(bytes_len, "big")

    result = bytes()

    result += _int_to_bytes(packet.type.value << 4 | packet.ver, 1)
    result += _int_to_bytes(packet.extensions[0][0] if packet.extensions else 0, 1)
    result += _int_to_bytes(packet.connection_id, 2)
    result += _int_to_bytes(packet.timestamp, 4)
    result += _int_to_bytes(packet.timestamp_diff, 4)
    result += _int_to_bytes(packet.wnd_size, 4)
    result += _int_to_bytes(packet.seq_nr, 2)
    result += _int_to_bytes(packet.ack_nr, 2)

    for idx, (_, ext_data) in enumerate(packet.extensions or []):
        result += (
            packet.extensions[idx + 1][0] if idx + 1 < len(packet.extensions) else 0
        ).to_bytes(1, "big")
        result += _int_to_bytes(len(ext_data), 1) + ext_data

    result += packet.data or b""

    return result
