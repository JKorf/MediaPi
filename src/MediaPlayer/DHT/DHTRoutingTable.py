from MediaPlayer.DHT.DHTNode import NodeState, NodeId, Node
from Shared.Logger import Logger
from Shared.Util import current_time


class Bucket:

    def __init__(self, min_id, max_id):
        self.nodes = []
        self.last_changed = current_time()
        self.min_id = min_id
        self.max_id = max_id

    def add_node(self, node):
        if len(self.nodes) < 8:
            self.nodes.append(node)
            self.last_changed = current_time()
            return True
        else:
            for cur_node in list(self.nodes):
                if cur_node.state == NodeState.Bad:
                    self.nodes.remove(cur_node)
                    self.last_changed = current_time()
                    self.nodes.append(node)
                    return True
            return False

    def __contains__(self, item):
        for node in self.nodes:
            if node.node_id == item.node_id:
                return True
        return False

    def can_contain(self, item):
        if self.min_id <= item.node_id < self.max_id:
            return True
        return False

    def find_node_by_id(self, node_id):
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def get_least_seen_good_node(self):
        self.sort()
        for node in self.nodes:
            if node.state != NodeState.Bad:
                return node
        return None

    def sort(self):
        self.nodes = sorted(self.nodes, key=lambda node: node.last_seen)


class RoutingTable:

    def __init__(self, own_node):
        self.buckets = []
        self.own_node = own_node

    @classmethod
    def create(cls):
        obj = cls(Node(NodeId.from_int(1233644844011859192182395734624983256215958799307), "0.0.0.0", 50000))
        obj.buckets.append(Bucket(NodeId.from_int(0), NodeId.from_bytes(bytearray([255] * 20))))
        return obj

    def add(self, node, splitting=False):
        for bucket in list(self.buckets):
            if bucket.can_contain(node):
                if node in bucket:
                    bucket.find_node_by_id(node.node_id).seen()
                    return
                added = bucket.add_node(node)
                if not splitting and added:
                    Logger.write(1, "DHT: Added node to bucket, now " + str(self.count_nodes()))
                if not added:
                    if self.split(bucket):
                        self.add(node)

    def split(self, bucket):
        # check if we can split
        if bucket.can_contain(self.own_node):
            Logger.write(1, "DHT: Splitting bucket")

            # split since we can fit our own id in this
            mid = NodeId.from_int((bucket.min_id.int_value + bucket.max_id.int_value) // 2)
            new_bucket_min = Bucket(bucket.min_id, mid)
            new_bucket_max = Bucket(mid, bucket.max_id)
            self.buckets.remove(bucket)
            self.buckets.append(new_bucket_min)
            self.buckets.append(new_bucket_max)
            for node in bucket.nodes:
                self.add(node, True)
            return True
        return False

    def count_nodes(self):
        total = 0
        for bucket in self.buckets:
            total += len(bucket.nodes)
        return total

    def find_node_by_id(self, id):
        for bucket in self.buckets:
            for node in bucket.nodes:
                if node.node_id == id:
                    return node
        return None

    def closest_nodes(self, id):
        result = []
        for bucket in self.buckets:
            for node in bucket.nodes:
                dist = node.node_id ^ id
                if len(result) < 8:
                    result.append((dist, node))
                    continue

                current_furthest = Node.get_furthest_from_list(result)
                if dist < current_furthest[0]:
                    result.append((dist, node))
                    result.remove(current_furthest)
        return [x[1] for x in result]