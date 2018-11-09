import abc

from MediaPlayer.TorrentStreaming.DHT.Util import TransactionIdManager
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from Shared.Logger import Logger


class QueryMessage:

    def __init__(self, node_message, send_at, on_response, on_timeout):
        self.message = node_message
        self.send_at = send_at
        self.on_response = on_response
        self.on_timeout = on_timeout


class NodeMessage:

    def __init__(self, ip, port, message):
        self.ip = ip
        self.port = port
        self.message = message


class BaseDHTMessage:

    def __init__(self, type):
        self.message_type = type
        self.transaction_id = None

    @abc.abstractmethod
    def to_bytes(self):
        return

    @staticmethod
    def from_bytes(bytes):
        try:
            data = Bencode.bdecode(bytes)
        except BTFailure:
            Logger.write(2, "DHT: Invalid dht message" + str(bytes))
            return None
        if b'y' not in data:
            Logger.write(2, "DHT: Unknown message: " + str(data))
            return None

        if data[b'y'] == b'r':
            # response
            return ResponseDHTMessage.from_dict(data)

        elif data[b'y'] == b'q':
            # query
            return QueryDHTMessage.from_dict(data)

        else:
            # error
            return ErrorDHTMessage.from_dict(data)


class QueryDHTMessage(BaseDHTMessage):

    @property
    def target(self):
        return self.args[b'target']

    @property
    def info_hash(self):
        return self.args[b'info_hash']

    @property
    def id(self):
        return self.args[b'id']

    @property
    def port(self):
        return self.args[b'port']

    @property
    def token(self):
        return self.args[b'token']

    def __init__(self, node_id, query, args):
        BaseDHTMessage.__init__(self, b'q')
        self.query = query
        self.args = args
        self.node_id = node_id
        self.transaction_id = TransactionIdManager.next_trans_id()
        if not self.args:
            self.args = dict()
        self.args[b'id'] = self.node_id

    @classmethod
    def create_ping(cls, node_id):
        return cls(node_id, b'ping', None)

    @classmethod
    def create_find_node(cls, node_id, target):
        dic = dict()
        dic[b'target'] = target
        return cls(node_id, b'find_node', dic)

    @classmethod
    def create_get_peers(cls, node_id, info_hash):
        dic = dict()
        dic[b'info_hash'] = info_hash
        return cls(node_id, b'get_peers', dic)

    @classmethod
    def create_announce(cls, node_id,  info_hash, port, token):
        dic = dict()
        dic[b'info_hash'] = info_hash
        dic[b'port'] = port
        dic[b'token'] = token
        return cls(node_id, b'announce_peer', dic)

    @classmethod
    def from_dict(cls, dict):
        if dict[b'q'] == b'ping':
            msg = QueryDHTMessage.create_ping(dict[b'a'][b'id'])
            msg.transaction_id = dict[b't']
            return msg
        elif dict[b'q'] == b'find_node':
            msg = QueryDHTMessage.create_find_node(dict[b'a'][b'id'], dict[b'a'][b'target'])
            msg.transaction_id = dict[b't']
            return msg
        elif dict[b'q'] == b'get_peers':
            msg = QueryDHTMessage.create_get_peers(dict[b'a'][b'id'], dict[b'a'][b'info_hash'])
            msg.transaction_id = dict[b't']
            return msg
        elif dict[b'q'] == b'announce_peers':
            msg = QueryDHTMessage.create_announce(dict[b'a'][b'id'], dict[b'a'][b'info_hash'], dict[b'a'][b'port'], dict[b'a'][b'token'])
            msg.transaction_id = dict[b't']
            return msg
        return None

    def to_bytes(self):
        result = dict()
        result[b't'] = self.transaction_id
        result[b'y'] = self.message_type
        result[b'q'] = self.query
        result[b'a'] = self.args
        return Bencode.bencode(result)


class ResponseDHTMessage(BaseDHTMessage):

    @property
    def id(self):
        return self.response[b'id']

    @property
    def nodes(self):
        return self.response[b'nodes']

    @property
    def values(self):
        return self.response[b'values']

    @property
    def token(self):
        return self.response[b'token']

    def __init__(self, transaction_id, response):
        BaseDHTMessage.__init__(self, b'r')
        self.transaction_id = transaction_id
        self.response = response
        if not self.response:
            self.response = dict()

    #  TODO Create methods

    def to_bytes(self):
        result = dict()
        result[b't'] = self.transaction_id
        result[b'y'] = self.message_type
        result[b'r'] = self.response
        return Bencode.bencode(result)

    @classmethod
    def from_dict(cls, dict):
        return cls(dict[b't'], dict[b'r'])

    @classmethod
    def create_ping_response(cls, node_id, transaction_id):
        response_dict = dict()
        response_dict[b'id'] = node_id
        return cls(transaction_id, response_dict)

    @classmethod
    def create_find_node_response(cls, node_id, transaction_id, nodes, values):
        response_dict = dict()
        response_dict[b'id'] = node_id
        if nodes is not None:
            response_dict[b'nodes'] = nodes
        else:
            response_dict[b'values'] = values
        return cls(transaction_id, response_dict)

    @classmethod
    def create_get_peers_response(cls, node_id, transaction_id, nodes, values, token):
        response_dict = dict()
        response_dict[b'id'] = node_id
        response_dict[b'token'] = token
        if nodes is not None:
            response_dict[b'nodes'] = nodes
        else:
            response_dict[b'values'] = values
        return cls(transaction_id, response_dict)

    @classmethod
    def create_announce_peer_response(cls, node_id, transaction_id):
        response_dict = dict()
        response_dict[b'id'] = node_id
        return cls(transaction_id, response_dict)


class ErrorDHTMessage(BaseDHTMessage):

    def __init__(self, transaction_id, errorcode, errormsg):
        BaseDHTMessage.__init__(self, b'e')
        self.transaction_id = transaction_id
        self.errorcode = errorcode
        self.errormsg = errormsg

    def to_bytes(self):
        result = dict()
        result[b't'] = self.transaction_id
        result[b'y'] = self.message_type
        result[b'e'] = [self.errorcode, self.errormsg]
        return Bencode.bencode(result)

    @classmethod
    def from_dict(cls, dict):
        error_list = dict[b'e']
        return cls(dict[b't'], error_list[0], error_list[1])