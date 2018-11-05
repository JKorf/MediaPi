from MediaPlayer.DHT2.Node import NodeState
from Shared.Util import current_time


class Bucket:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.max_nodes = 8
        self.nodes = []
        self.last_changed = 0

    def split(self):
        self.start += (self.end - self.start) // 2
        split_nodes = [x for x in self.nodes if x.int_id < self.start]
        self.nodes = [x for x in self.nodes if x.int_id >= self.start]
        return split_nodes

    def fits(self, id):
        return self.start <= id < self.end

    def full(self):
        return len([x for x in self.nodes if x.state != NodeState.Bad]) == self.max_nodes

    def add_node(self, node):
        if len(self.nodes) >= self.max_nodes:
            self.nodes = [x for x in self.nodes if x.state != NodeState.Bad]

        self.nodes.append(node)
        self.last_changed = current_time()