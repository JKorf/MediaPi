import os
import socket

from MediaPlayer.TorrentStreaming.DHT.Bucket import Bucket
from MediaPlayer.TorrentStreaming.DHT.Tasks import PingTask

from MediaPlayer.TorrentStreaming.DHT.Node import Node
from Shared.Logger import Logger
from Shared.Util import current_time


class Table:

    def __init__(self, dht_engine):
        self.dht_engine = dht_engine
        self.buckets = []
        self.buckets.append(Bucket(0, pow(2, 160)))

    def init_nodes(self, known_nodes):
        for node in known_nodes:
            self.add_node(node)

        if self.total_nodes() == 0:
            self.add_node(Node(socket.gethostbyname("router.bittorrent.com"), 6881, os.urandom(20)))

    def total_nodes(self):
        return sum(len(x.nodes) for x in self.buckets)

    def add_node(self, node):
        node.seen()
        for bucket in self.buckets:
            if bucket.fits(node.int_id):
                self.add_to_bucket(bucket, node)
                return

    def update_node(self, id):
        for bucket in self.buckets:
            for node in bucket.nodes:
                if node.byte_id == id:
                    node.seen()
                    bucket.last_update = current_time()
                    return

    def fail_node(self, ip, port):
        for bucket in self.buckets:
            for node in bucket.nodes:
                if node.ip == ip and node.port == port:
                    node.fail()
                    return

    def contains_node(self, id_bytes):
        for bucket in self.buckets:
            if bucket.contains_node(id_bytes):
                return True
        return False

    def get_node(self, id):
        for bucket in self.buckets:
            node = bucket.get_node(id)
            if node is not None:
                return node

    def get_closest_nodes(self, id):
        int_id = int(id.hex(), 16)
        all_nodes = self.all_nodes()
        return sorted(all_nodes, key=lambda x: x.distance(int_id))[:8]

    def all_nodes(self):
        result = []
        for bucket in list(self.buckets):
            result.extend(bucket.nodes)
        return result

    def add_to_bucket(self, bucket, new_node):
        if bucket.full():
            questionable_nodes = bucket.questionable_nodes()
            if len(questionable_nodes) != 0:
                task = PingTask(self.dht_engine, self.dht_engine.own_node.byte_id, questionable_nodes[0].ip, questionable_nodes[0].port)
                task.on_complete = lambda: self.add_to_bucket(bucket, new_node)  # when the ping returns the node is either bad or no longer questionable
                task.execute()
                return

            if bucket.fits(self.dht_engine.own_node.int_id):
                Logger().write(1, "DHT: Bucket is full, splitting")
                new_range = (bucket.end - bucket.start) // 2
                new_bucket = Bucket(bucket.start, bucket.start + new_range)
                split_nodes = bucket.split()
                for node in split_nodes:
                    new_bucket.add_node(node)

                self.buckets.append(new_bucket)
                self.add_node(new_node)
            else:
                Logger().write(1, "DHT: Skipping adding of node, bucket is full")
        else:
            bucket.add_node(new_node)
            Logger().write(1, "DHT: Node " + str(new_node.int_id) + " added to bucket")
