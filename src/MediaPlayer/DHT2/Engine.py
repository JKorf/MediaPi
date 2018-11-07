import os

import time
from random import Random

from MediaPlayer.DHT2.Messages import ResponseDHTMessage
from MediaPlayer.DHT2.Node import Node, NodeState
from MediaPlayer.DHT2.Socket import Socket
from MediaPlayer.DHT2.Table import Table
from MediaPlayer.DHT2.Tasks import FindNodeTask, GetPeersTask, PingTask
from MediaPlayer.DHT2.Util import TokenManager
from MediaPlayer.Engine.Engine import Engine
from MediaPlayer.Util.Enums import PeerSource
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import Singleton, current_time


class DHTEngine(metaclass=Singleton):

    def __init__(self):
        self.own_node = None

        self.routing_table = Table(self)
        self.socket = Socket(Settings.get_int("dht_port"), self.on_node_seen, self.on_node_timeout, self.on_query)
        self.engine = Engine("DHT Engine", 5000)
        self.engine.queue_repeating_work_item("DHT Refresh buckets", 1000 * 60, self.refresh_buckets, False)
        self.engine.queue_repeating_work_item("DHT Save nodes", 1000 * 60 * 5, self.save_nodes, False)

        self.running_tasks = []

        EventManager.register_event(EventType.RequestPeers, self.search_peers)
        EventManager.register_event(EventType.NewDHTNode, self.add_node)

    def add_node(self, ip, port):
        self.start_task(PingTask(self, self.own_node.byte_id, ip, port))

    def on_node_seen(self, ip, port, id):
        if self.routing_table.contains_node(id):
            self.routing_table.update_node(id)
        else:
            self.routing_table.add_node(Node(ip, port, id))

    def on_node_timeout(self, ip, port):
        self.routing_table.fail_node(ip, port)

    def on_query(self, ip, port, message):
        if message.query == b"ping":
            response = ResponseDHTMessage.create_ping_response(self.own_node.byte_value, message.transaction_id)
            self.socket.send_response(response, ip, port)
        elif message.query == b"find_nodes":
            found_node = self.routing_table.get_node(message.target)
            if found_node is not None:
                self.socket.send_response(ResponseDHTMessage.create_find_node_response(self.own_node.byte_id, message.transaction_id, None, found_node.byte_id), ip, port)
            else:
                closest_nodes = self.routing_table.get_closest_nodes(message.target)
                self.socket.send_response(ResponseDHTMessage.create_find_node_response(self.own_node.byte_id, message.transaction_id, bytes(Node.node_bytes_multiple(closest_nodes)), None), ip, port)
        elif message.query == b"get_peers":
            closest_nodes = self.routing_table.get_closest_nodes(message.info_hash)
            token = TokenManager.generate_token(Node(ip, port, message.id))
            self.socket.send_response(ResponseDHTMessage.create_get_peers_response(self.own_node.byte_id, message.transaction_id, bytes(Node.node_bytes_multiple(closest_nodes)), None, token), ip, port)
        elif message.query == b"announce_peer":
            pass
        else:
            Logger.write(2, "DHT: received unknown query: " + str(message.query))

    def start(self):
        byte_id, nodes = self.load_nodes()
        if byte_id is None:
            byte_id = os.urandom(20)
        self.own_node = Node(0, 0, byte_id)
        self.routing_table.init_nodes(nodes)

        self.socket.start()
        self.engine.start()
        self.start_task(FindNodeTask(self, self.own_node.byte_id, self.own_node, self.routing_table.all_nodes()))

    def search_peers(self, torrent):
        self.start_task(GetPeersTask(self, self.own_node.byte_id, torrent.info_hash.sha1_hashed_bytes, self.routing_table.get_closest_nodes(hash)), lambda x: EventManager.throw_event(EventType.PeersFound, [x.found_peers, PeerSource.DHT]))

    def start_task(self, task, on_complete=None):
        task.on_complete = lambda: self.end_task(task, on_complete)
        self.running_tasks.append(task)
        task.execute()

    def end_task(self, task, on_complete):
        Logger.write(2, "DHT: " + type(task).__name__ + " completed in " + str(task.end_time - task.start_time) + "ms")
        self.running_tasks.remove(task)
        if on_complete:
            on_complete(task)

    def refresh_buckets(self):
        for bucket in list(self.routing_table.buckets):
            if current_time() - bucket.last_changed > 1000 * 60 * 15:
                self.start_task(FindNodeTask(self, self.own_node.byte_id, Random().randint(bucket.start, bucket.end), self.routing_table.all_nodes()))
        return True

    def save_nodes(self):
        all_nodes = bytearray()
        all_nodes.extend(self.own_node.byte_id)
        for node in self.routing_table.all_nodes():
            if node.node_state != NodeState.Bad:
                all_nodes.extend(node.node_bytes())

        Logger.write(2, "DHT: Saving " + str(len(all_nodes) // 26) + " nodes")
        with open('dht.data', 'wb') as w:
            w.write(all_nodes)
        return True

    def load_nodes(self):
        try:
            with open("dht.data", "rb") as file:
                data = file.read()
            nodes = Node.from_bytes_multiple(data[20:])
            Logger.write(2, "DHT: Starting with " + str(len(nodes)) + " nodes")
            return data[0:20], nodes
        except FileNotFoundError:
            return None, []