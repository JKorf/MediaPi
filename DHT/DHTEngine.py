from DHT.DHTMessages import QueryDHTMessage, ResponseDHTMessage
from DHT.DHTNode import Node, NodeId, NodeState
from DHT.DHTRoutingTable import RoutingTable
from DHT.DHTSocket import DHTSocket
from DHT.DHTTasks import InitializeTask, QueryTask, GetPeersTask, RefreshBucketTask
from DHT.DHTTokenManager import TokenManager
from Shared.Logger import Logger
from Shared.Util import current_time
from TorrentSrc.Engine.Engine import Engine


class DHTEngine:

    def __init__(self):
        self.runner = Engine("DHT Engine", 5)
        self.socket = DHTSocket(self, 50000)
        self.routing_table = RoutingTable.create()

        self.torrents = dict()
        self.last_table_save = current_time()

    def start(self):
        Logger.write(2, "DHT: Start engine")
        self.runner.queue_repeating_work_item("DHT update", 1000, self.update)
        self.runner.start()
        self.socket.start()
        known_nodes = self.load_table()
        InitializeTask(self, known_nodes).execute()

    def update(self):
        if current_time() - self.last_table_save > 5*60*1000:  # 5 min
            self.save_table()

        for bucket in self.routing_table.buckets:
            if current_time() - bucket.last_changed > 15*60*1000:  # 15 min
                Logger.write(1, "DHT: Refreshing bucket")
                bucket.last_changed = current_time()
                RefreshBucketTask(self, bucket).execute()

        return True

    def save_table(self):
        self.last_table_save = current_time()
        all_nodes = bytearray()
        for bucket in self.routing_table.buckets:
            for node in bucket.nodes:
                if node.state != NodeState.Bad:
                    all_nodes.extend(node.node_bytes())

        Logger.write(1, "DHT: Saving " + str(len(all_nodes) // 26) + " nodes")
        with open('dht.data', 'wb') as w:
            w.write(all_nodes)

    def add_node_by_ip_port(self, ip, port):
        QueryTask(self, QueryDHTMessage.create_ping(self.routing_table.own_node.node_id.byte_value), Node(NodeId.from_int(0), ip, port)).execute()

    def add_node(self, node):
        QueryTask(self, QueryDHTMessage.create_ping(self.routing_table.own_node.node_id.byte_value), node).execute()

    def get_peers(self, torrent, handler):
        GetPeersTask(self, torrent, handler).execute()

    def load_table(self):
        try:
            in_file = open("dht.data", "rb")
            data = in_file.read()
            in_file.close()
            return Node.from_bytes_multiple(data)
        except FileNotFoundError:
            return []

    def stop(self):
        self.runner.stop()
        self.socket.stop()

    def handle_query(self, message_wrapper):
        if message_wrapper.message.query == b'ping':
            response = ResponseDHTMessage.create_ping_response(self.routing_table.own_node.node_id.byte_value, message_wrapper.message.transaction_id)
            self.socket.send(response, message_wrapper.node)

        elif message_wrapper.message.query == b'find_node':
            node = self.routing_table.find_node_by_id(NodeId.from_bytes(message_wrapper.message.target))
            if node is not None:
                response = ResponseDHTMessage.create_find_node_response(self.routing_table.own_node.node_id.byte_value, message_wrapper.message.transaction_id, None, node.node_id.byte_value)
            else:
                closest_nodes = self.routing_table.closest_nodes(NodeId.from_bytes(message_wrapper.message.target))
                response = ResponseDHTMessage.create_find_node_response(self.routing_table.own_node.node_id.byte_value, message_wrapper.message.transaction_id, bytes(Node.node_bytes_multiple(closest_nodes)), None)
            self.socket.send(response, message_wrapper.node)

        elif message_wrapper.message.query == b'get_peers':
            info_hash = message_wrapper.message.info_hash
            token = TokenManager.generate_token(message_wrapper.node)

            if info_hash in self.torrents:
                nodes = Node.node_bytes_multiple(self.torrents[info_hash])
                response = ResponseDHTMessage.create_get_peers_response(self.routing_table.own_node.node_id.byte_value, message_wrapper.message.transaction_id, None, bytes(Node.node_bytes_multiple(nodes)), token)
            else:
                closest_nodes = self.routing_table.closest_nodes(NodeId.from_bytes(info_hash))
                response = ResponseDHTMessage.create_get_peers_response(self.routing_table.own_node.node_id.byte_value, message_wrapper.message.transaction_id, bytes(Node.node_bytes_multiple(closest_nodes)), None, token)
            self.socket.send(response, message_wrapper.node)

        elif message_wrapper.message.query == b'announce_peer':
            pass
        else:
            Logger.write(2, "DHT: Unknown query: " + str(message_wrapper.message.query))

