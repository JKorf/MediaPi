import socket

from DHT.DHTMessages import QueryDHTMessage
from DHT.DHTNode import Node, NodeId, NodeState
from Shared.Logger import Logger
from TorrentSrc.Util.Util import ip_port_from_bytes_multiple, ip_port_from_bytes


class QueryTask:

    def __init__(self, engine, query_message, node):
        self.engine = engine
        self.query_message = query_message
        self.node = node
        self.hook_id = 0
        self.on_done = None

    def execute(self):
        self.hook_id = self.engine.socket.register_waiting(self.on_message_done)
        self.engine.socket.send(self.query_message, self.node)

    def on_message_done(self, received_response, message_wrapper):
        if message_wrapper.node.ip != self.node.ip or message_wrapper.node.port != self.node.port or message_wrapper.message is None or message_wrapper.message.transaction_id != self.query_message.transaction_id:
            return

        self.engine.socket.deregister_waiting(self.hook_id)
        if not received_response:
            message_wrapper.node.failed_communications += 1
            if message_wrapper.node.state != NodeState.Bad:
                self.execute()
                return
        if self.on_done is not None:
            self.on_done(received_response, message_wrapper)


class InitializeTask:

    def __init__(self, engine, nodes):
        self.engine = engine
        self.initialNodes = nodes
        self.current_closest_nodes = []
        self.outstanding_requests = 0
        if self.initialNodes is None:
            self.initialNodes = []

    def execute(self):
        Logger.write(2, "DHT: Init task with " + str(len(self.initialNodes)) + " nodes")

        if len(self.initialNodes) > 0:
            for node in self.initialNodes:
                self.engine.add_node(node)
            self.find_node(self.initialNodes)
        else:
            default_node = Node(NodeId.create(), socket.gethostbyname("router.bittorrent.com"), 6881)
            self.find_node([default_node])

    def find_node(self, nodes):
        closest_not_used, self.current_closest_nodes = Node.closest_nodes(self.engine.routing_table.own_node.node_id, self.current_closest_nodes, nodes)
        for node in closest_not_used:
            self.outstanding_requests += 1
            request = QueryDHTMessage.create_find_node(self.engine.routing_table.own_node.node_id.byte_value, self.engine.routing_table.own_node.node_id.byte_value)
            query_task = QueryTask(self.engine, request, node)
            query_task.on_done = self.find_node_completed
            query_task.execute()

    def find_node_completed(self, response_received, message_wrapper):
        self.outstanding_requests -= 1
        if response_received:
            if message_wrapper.message.response and b'nodes' in message_wrapper.message.response:
                self.find_node(Node.from_bytes_multiple(message_wrapper.message.nodes))
        if self.outstanding_requests == 0:
            Logger.write(2, "DHT: Initialize done")


class GetPeersTask:

    def __init__(self, engine, torrent, on_done):
        self.torrent = torrent
        self.info_hash = NodeId.from_bytes(torrent.info_hash.sha1_hashed_bytes)
        self.engine = engine
        self.closest_nodes = []
        self.queried_nodes = []
        self.found_nodes = []
        self.outstanding_requests = 0
        self.on_done = on_done

    def execute(self):
        Logger.write(2, "DHT: Going to search for peers for torrent")
        new_nodes = self.engine.routing_table.closest_nodes(self.info_hash)
        closest_nodes, self.closest_nodes = Node.closest_nodes(self.info_hash, self.closest_nodes, new_nodes)
        for node in closest_nodes:
            self.get_peers(node)

    def get_peers(self, node):
        dist = node.node_id ^ self.info_hash
        self.queried_nodes.append((dist, node))
        self.outstanding_requests += 1

        msg = QueryDHTMessage.create_get_peers(self.engine.routing_table.own_node.node_id.byte_value, self.info_hash.byte_value)
        task = QueryTask(self.engine, msg, node)
        task.on_done = self.get_peers_done
        task.execute()

    def get_peers_done(self, response_received, message_wrapper):
        self.outstanding_requests -= 1

        if response_received:
            node = self.engine.routing_table.find_node_by_id(message_wrapper.node.node_id)
            if node is not None:
                if b'token' in message_wrapper.message.response:
                    node.token = message_wrapper.message.token
            if b'values' in message_wrapper.message.response:
                for port_bytes in message_wrapper.message.values:
                    self.found_nodes.append(ip_port_from_bytes(port_bytes))
            elif b'nodes' in message_wrapper.message.response:
                new_nodes = Node.from_bytes_multiple(message_wrapper.message.nodes)
                closest_nodes, self.closest_nodes = Node.closest_nodes(self.info_hash, self.closest_nodes, new_nodes)
                for node in closest_nodes:
                    self.get_peers(node)

        if self.outstanding_requests == 0:
            Logger.write(2, "DHT: Found " + str(len(self.found_nodes)) + " peers for torrent")
            self.on_done(self.torrent, self.found_nodes)


class RefreshBucketTask:

    def __init__(self, engine, bucket):
        self.engine = engine
        self.bucket = bucket

    def execute(self):
        if len(self.bucket.nodes) == 0:
            return

        # Get least seen
        node = self.bucket.get_least_seen_good_node()
        if node is not None:
            self.query_node(node)

    def query_node(self, node):
        msg = QueryDHTMessage.create_find_node(self.engine.routing_table.own_node.node_id.byte_value, node.node_id.byte_value)
        task = QueryTask(self.engine, msg, node)
        task.on_done = self.query_node_completed
        task.execute()

    def query_node_completed(self, response_received, message_wrapper):
        if not response_received:
            node = self.bucket.get_least_seen_good_node()
            if node is not None:
                self.query_node(node)

