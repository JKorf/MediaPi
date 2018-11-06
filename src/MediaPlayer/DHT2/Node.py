from enum import Enum

from MediaPlayer.Util.Network import read_bytes, write_bytes
from MediaPlayer.Util.Util import ip_port_from_bytes, ip_port_to_bytes
from Shared.Util import current_time


class Node:

    @property
    def node_state(self):
        if self.request_timeouts >= 2:
            return NodeState.Bad
        if current_time() - self.last_response > 1000 * 60 * 15:
            return NodeState.Questionable
        return NodeState.Good

    def __init__(self, ip, port, id):
        self.byte_id = id
        self.int_id = int(self.byte_id.hex(), 16)
        self.ip = ip
        self.port = port

        self.last_response = 0
        self.request_timeouts = 0

    def distance(self, node_id):
        return self.int_id | node_id

    def seen(self):
        self.last_response = current_time()
        self.request_timeouts = 0

    def fail(self):
        self.request_timeouts += 1

    @staticmethod
    def from_bytes(data):
        offset, id = read_bytes(data, 20, 0)
        ip, port = ip_port_from_bytes(data[20: 26])
        return Node(ip, port, id)

    @staticmethod
    def from_bytes_multiple(data):
        result = []
        for i in range(int(len(data) / 26)):
            result.append(Node.from_bytes(data[(i * 26): (i * 26) + 26]))
        return result

    def ip_port_bytes(self):
        result = bytearray(6)
        write_bytes(result, ip_port_to_bytes(self.ip, self.port), 0)
        return result

    def node_bytes(self):
        result = bytearray(26)
        write_bytes(result, self.byte_id, 0)
        write_bytes(result, ip_port_to_bytes(self.ip, self.port), 20)
        return result


class NodeState:

    Good = 2,
    Questionable = 1,
    Bad = 0
