from random import Random
from threading import Lock

from MediaPlayer.DHT2.Node import Node
from MediaPlayer.DHT2.Messages import QueryDHTMessage
from MediaPlayer.DHT2.Util import DHTTaskState
from MediaPlayer.Util.Util import ip_port_from_bytes
from Shared.Logger import Logger
from Shared.Util import current_time


class BaseTask:

    def __init__(self, dht_engine):
        self.dht_engine = dht_engine
        self.on_complete = None

        self.max_outstanding_requests = 5
        self.outstanding_requests = 0
        self.state = DHTTaskState.Initial
        self.start_time = 0
        self.end_time = 0

    def execute(self):
        self.start_time = current_time()
        self.state = DHTTaskState.Running
        self.execute_internal()

    def send_request(self, msg, ip, port, on_response, on_timeout):
        self.outstanding_requests += 1
        self.dht_engine.socket.send_query(msg,
                                            ip,
                                            port,
                                            lambda data: self.on_response_internal(on_response, data),
                                            lambda: self.on_response_timeout(on_timeout))

    def on_response_internal(self, handler, data):
        self.outstanding_requests -= 1
        handler(data)

    def on_response_timeout(self, handler):
        self.outstanding_requests -= 1
        handler()

    def complete(self):
        self.end_time = current_time()
        if self.on_complete:
            self.on_complete()
        self.state = DHTTaskState.Done


class PingTask(BaseTask):

    def __init__(self, dht_engine, node_id, ip, port):
        super().__init__(dht_engine)
        self.node_id = node_id
        self.ip = ip
        self.port = port

    def execute_internal(self):
        request = QueryDHTMessage.create_ping(self.node_id)
        self.send_request(request, self.ip, self.port, self.ping_response, self.ping_timeout)

    def ping_response(self, data):
        Logger.write(1, "DHT: Ping response received")
        self.complete()

    def ping_timeout(self):
        Logger.write(1, "DHT: Ping timed out")
        self.complete()


class FindNodeTask(BaseTask):

    def __init__(self, dht_engine, node_id, target, nodes):
        super().__init__(dht_engine)
        self.node_id = node_id
        self.target = target
        self.found_nodes = 0
        self.available_nodes = []
        self.closest_nodes = []
        self.closest_nodes_lock = Lock()
        self.append_nodes(nodes)

    def execute_internal(self):
        self.request_nodes()
        self.check_done()

    def request_nodes(self):
        to_request = max(self.max_outstanding_requests - self.outstanding_requests, len(self.available_nodes))
        requested = 0
        for node in list(self.available_nodes):
            request = QueryDHTMessage.create_find_node(self.node_id, self.target.byte_id)
            self.send_request(request, node.ip, node.port, self.find_node_response, self.find_node_timeout)
            self.available_nodes.remove(node)
            requested += 1
            if requested >= to_request:
                break

    def find_node_response(self, data):
        if b"nodes" in data.response:
            Logger.write(1, "DHT: FindNode request got a response with " + str(len(data.nodes) // 26) + " nodes")
            self.found_nodes += 1
            found_nodes = Node.from_bytes_multiple(data.nodes)
            self.append_nodes(found_nodes)
            self.request_nodes()
        self.check_done()

    def append_nodes(self, nodes):
        with self.closest_nodes_lock:
            for node in nodes:
                if len([x for x in self.closest_nodes if x.node.byte_id == node.byte_id]) == 0:
                    self.closest_nodes.append(CloseNode(node))

            self.closest_nodes.sort(key=lambda x: x.node.distance(self.target.int_id))

            for node in self.closest_nodes[:10]:
                if node.requested:
                    continue

                node.requested = True
                self.available_nodes.append(node.node)

    def find_node_timeout(self):
        Logger.write(1, "DHT: FindNode request timed out")
        self.check_done()

    def check_done(self):
        if self.outstanding_requests == 0:
            Logger.write(2, "DHT: FindNode found " + str(self.found_nodes) + " nodes")
            self.complete()


class GetPeersTask(BaseTask):

    def __init__(self, dht_engine, id, info_hash, nodes):
        super().__init__(dht_engine)
        self.id = id
        self.info_hash = info_hash
        self.info_hash_int = int(info_hash.hex, 16)
        self.available_nodes = []
        self.closest_nodes = []
        self.closest_nodes_lock = Lock()
        self.found_peers = []
        self.append_nodes(nodes)

    def execute_internal(self):
        self.request_nodes()

    def request_nodes(self):
        to_request = max(self.max_outstanding_requests - self.outstanding_requests, len(self.available_nodes))
        requested = 0
        for node in list(self.available_nodes):
            request = QueryDHTMessage.create_get_peers(self.id, self.info_hash)
            self.send_request(request, node.ip, node.port, self.on_response, self.on_timeout)
            self.available_nodes.remove(node)
            requested += 1
            if requested >= to_request:
                break

    def on_response(self, data):
        if b'values' in data.response:
            Logger.write(1, "DHT: GetPeers request got values response")
            for peer_data in data.values:
                self.found_peers.append(ip_port_from_bytes(peer_data))

        elif b'nodes' in data.response:
            Logger.write(1, "DHT: GetPeers request got nodes response")
            new_nodes = Node.from_bytes_multiple(data.nodes)
            self.append_nodes(new_nodes)
            self.request_nodes()

        self.check_done()

    def append_nodes(self, nodes):
        with self.closest_nodes_lock:
            for node in nodes:
                if len([x for x in self.closest_nodes if x.node.byte_id == node.byte_id]) == 0:
                    self.closest_nodes.append(CloseNode(node))

            self.closest_nodes.sort(key=lambda x: x.node.distance(self.info_hash_int))

            for node in self.closest_nodes[:10]:
                if node.requested:
                    continue

                node.requested = True
                self.available_nodes.append(node.node)

    def on_timeout(self):
        Logger.write(1, "DHT: GetPeers request timed out")
        self.check_done()

    def check_done(self):
        if self.outstanding_requests == 0:
            Logger.write(2, "DHT: GetPeers found " + str(self.found_peers) + " peers")
            self.complete()


class CloseNode:
    def __init__(self, node):
        self.node = node
        self.requested = False
