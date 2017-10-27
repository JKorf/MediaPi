import os
from enum import Enum

from Shared.Util import current_time
from TorrentSrc.Util.Network import write_bytes, read_bytes
from TorrentSrc.Util.Util import ip_port_to_bytes, ip_port_from_bytes


class NodeId:

    def __init__(self):
        self.int_value = 0
        self.byte_value = None

    @classmethod
    def create(cls):
        return cls.from_bytes(os.urandom(20))

    @classmethod
    def from_int(cls, data):
        obj = cls()
        obj.int_value = data
        obj.byte_value = data.to_bytes(20, byteorder='big')
        return obj

    @classmethod
    def from_bytes(cls, data):
        obj = cls()
        obj.byte_value = data
        obj.int_value = int.from_bytes(data, byteorder='big')
        return obj

    def __add__(self, other):
        return NodeId.from_int(self.int_value + other.int_value)

    def __sub__(self, other):
        return NodeId.from_int(self.int_value - other.int_value)

    def __floordiv__(self, other):
        return NodeId.from_int(self.int_value // other)

    def __eq__(self, other):
        for i in range(len(self.byte_value)):
            if self.byte_value[i] != other.byte_value[i]:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __ge__(self, other):
        if self.int_value >= other.int_value:
            return True
        return False

    def __gt__(self, other):
        if self.int_value > other.int_value:
            return True
        return False

    def __le__(self, other):
        if self.int_value <= other.int_value:
            return True
        return False

    def __lt__(self, other):
        if self.int_value < other.int_value:
            return True
        return False

    def __xor__(self, other):
        result = bytearray(20)
        for i in range(20):
            result[i] = self.byte_value[i] ^ other.byte_value[i]
        return NodeId.from_bytes(result)


class NodeState(Enum):
    Unknown = 0,
    Good = 1,
    Questionable = 2,
    Bad = 3


class Node:

    @property
    def state(self):
        if self.failed_communications > 2:
            return NodeState.Bad
        if current_time() - self.last_seen > 15 * 60 * 1000:
            return NodeState.Questionable
        return NodeState.Good

    def __init__(self, node_id, ip, port):
        self.node_id = node_id
        self.ip = ip
        self.port = port
        self.last_seen = 0
        self.failed_communications = 0
        self.token = None

    def __eq__(self, other):
        return self.node_id == other.node_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def seen(self):
        self.last_seen = current_time()
        self.failed_communications = 0

    def node_bytes(self):
        result = bytearray(26)
        write_bytes(result, self.node_id.byte_value, 0)
        write_bytes(result, ip_port_to_bytes(self.ip, self.port), 20)
        return result

    def ip_port_bytes(self):
        result = bytearray(6)
        write_bytes(result, ip_port_to_bytes(self.ip, self.port), 0)
        return result

    @staticmethod
    def node_bytes_multiple(nodes):
        result = bytearray()
        for node in nodes:
            result.extend(node.node_bytes())
        return result

    @staticmethod
    def ip_port_bytes_multiple(nodes):
        result = bytearray()
        for node in nodes:
            result.extend(node.ip_port_bytes())
        return result

    @staticmethod
    def from_bytes(data):
        offset, id = read_bytes(data, 20, 0)
        ip, port = ip_port_from_bytes(data[20: 26])
        return Node(NodeId.from_bytes(id), ip, port)

    @staticmethod
    def from_bytes_multiple(data):
        result = []
        for i in range(int(len(data) / 26)):
            result.append(Node.from_bytes(data[(i * 26): (i * 26) + 26]))
        return result

    @staticmethod
    def closest_nodes(target_id, closest_nodes, new_available_nodes):
        result = []
        for node in new_available_nodes:
            if node.node_id in [x[1].node_id for x in closest_nodes]:
                continue

            node_to_target_dist = node.node_id ^ target_id
            if len(closest_nodes) < 8:
                closest_nodes.append((node_to_target_dist, node))
                result.append(node)
                continue

            current_furthest = Node.get_furthest_from_list(closest_nodes)
            if node_to_target_dist < current_furthest[0]:
                result.append(node)
                closest_nodes.remove(current_furthest)
                closest_nodes.append((node_to_target_dist, node))

        return result, closest_nodes

    @staticmethod
    def get_furthest_from_list(nodes):
        furthest = None
        for dist, node in nodes:
            if furthest is None:
                furthest = (dist, node)
                continue

            if dist > furthest[0]:
                furthest = (dist, node)
        return furthest

