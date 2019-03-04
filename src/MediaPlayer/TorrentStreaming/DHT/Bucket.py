from MediaPlayer.TorrentStreaming.DHT.Node import NodeState
from Shared.Logger import Logger
from Shared.Util import current_time


class Bucket:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.max_nodes = 8
        self.nodes = []
        self.last_changed = 0

        Logger().write(1, "Creating new bucket from " + str(self.start) + " to " + str(self.end))

    def split(self):
        self.start += (self.end - self.start) // 2
        Logger().write(1, "DHT: Splitting bucket, new range: " + str(self.start) + " to " + str(self.end))
        split_nodes = [x for x in self.nodes if x.int_id < self.start]
        self.nodes = [x for x in self.nodes if x.int_id >= self.start]
        return split_nodes

    def fits(self, id):
        return self.start <= id < self.end

    def contains_node(self, id_bytes):
        return len([x for x in self.nodes if x.byte_id == id_bytes]) == 1

    def full(self):
        return len([x for x in self.nodes if x.node_state != NodeState.Bad]) == self.max_nodes

    def add_node(self, node):
        if len(self.nodes) >= self.max_nodes:
            self.nodes = [x for x in self.nodes if x.node_state != NodeState.Bad]

        self.nodes.append(node)
        self.last_changed = current_time()

    def get_node(self, id):
        nodes = [x for x in self.nodes if x.byte_id == id]
        if len(nodes) != 0:
            return nodes[0]
        return None

    def questionable_nodes(self):
        return [x for x in self.nodes if x.node_state == NodeState.Questionable]