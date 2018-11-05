from enum import Enum


class Node:

    def __init__(self, ip, port, id):
        self.byte_id = id
        self.int_id = int(self.byte_id.hex(), 16)
        self.ip = ip
        self.port = port

        self.last_response = 0
        self.request_timeouts = 0
        self.state = NodeState.Bad

    def distance(self, node):
        return self.int_id | node.int_id


class NodeState:

    Good = 2,
    Questionable = 1,
    Bad = 0