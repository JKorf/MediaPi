import os
import socket

from MediaPlayer.DHT2.Bucket import Bucket
from MediaPlayer.DHT2.Node import Node
from Shared.Logger import Logger


class Table:

    def __init__(self, own_id, known_nodes):
        self.own_id = own_id
        self.buckets = []
        self.buckets.append(Bucket(0, pow(2, 160)))

        for node in known_nodes:
            self.add_node(node)

        if self.total_nodes() == 0:
            self.add_node(Node(socket.gethostbyname("router.bittorrent.com"), 6881, os.urandom(20)))

    def total_nodes(self):
        return sum(len(x.nodes) for x in self.buckets)

    def add_node(self, node):
        for bucket in self.buckets:
            if bucket.fits(node.int_id):
                self.add_to_bucket(bucket, node)

    def add_to_bucket(self, bucket, node):
        if bucket.full():
            if bucket.fits(self.own_id):
                split_nodes = bucket.split()
                new_range = (bucket.end - bucket.start) // 2
                new_bucket = Bucket(bucket.start, bucket.end + new_range)
                for node in split_nodes:
                    new_bucket.add_node(node)
                self.buckets.append(new_bucket)
                if new_bucket.fits(node.int_id):
                    self.add_to_bucket(new_bucket, node)
                else:
                    self.add_to_bucket(bucket, node)
            else:
                Logger.write(2, "Skipping adding of node, bucket is full")
        else:
            bucket.add_node(node)
