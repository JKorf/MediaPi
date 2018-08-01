from socket import socket, AF_INET, SOCK_DGRAM
from threading import Lock

from MediaPlayer.DHT.DHTMessages import BaseDHTMessage, QueryDHTMessage, ResponseDHTMessage, ErrorDHTMessage
from MediaPlayer.DHT.DHTNode import NodeId, Node
from MediaPlayer.DHT.DHTTokenManager import TransactionIdManager
from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class DHTSocket:

    def __init__(self, engine, port):
        self.port = port
        self.engine = engine
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.receive_thread = CustomThread(self.__socket_receive, "DHT Receive thread", [])
        self.running = False

        self.last_send = 0
        self.pending_messages = []
        self.received_messages = []
        self.to_send_messages = []

        self.on_waiting_done = []
        self.register_id = 0
        self.register_lock = Lock()

    def can_send(self):
        # return len(self.pending_messages) < 5 and len(self.to_send_messages) > 0 and current_time() - self.last_send > 5
        return len(self.to_send_messages) > 0 and current_time() - self.last_send > 5

    def get_next_register_id(self):
        with self.register_lock:
            this_id = self.register_id
            self.register_id += 1
        return this_id

    def register_waiting(self, handler):
        id = self.get_next_register_id()
        self.on_waiting_done.append((id, handler))
        return id

    def deregister_waiting(self, id):
        self.on_waiting_done = [x for x in self.on_waiting_done if x[0] != id]

    def start(self):
        self.running = True
        self.socket.bind(('0.0.0.0', self.port))
        self.engine.runner.queue_repeating_work_item("DHT Communication", 5, self.communication_handler)
        self.receive_thread.start()
        Logger.write(2, "DHT: Socket running")

    def communication_handler(self):
        self.__send()
        self.__receive()
        self.__check_outstanding()
        return True

    def __socket_receive(self):
        while self.running:
            try:
                data, sender = self.socket.recvfrom(2048)
                msg_object = BaseDHTMessage.from_bytes(data)
                if msg_object is None:
                    continue

                msg = MessageWrapper(msg_object, Node(NodeId.from_int(0), sender[0], sender[1]))
                self.received_messages.append(msg)
            except OSError:
                continue

    def __receive(self):
        if len(self.received_messages) == 0:
            return

        message_wrapper = self.received_messages.pop(0)
        if isinstance(message_wrapper.message, ErrorDHTMessage):
            Logger.write(1, "Received Error? " + str(message_wrapper.message.errormsg))
            return

        message_wrapper.node.node_id = NodeId.from_bytes(message_wrapper.message.id)
        node = self.engine.routing_table.find_node_by_id(message_wrapper.node.node_id)
        if node is None:
            node = message_wrapper.node
            self.engine.routing_table.add(node)
        node.seen()

        if isinstance(message_wrapper.message, ResponseDHTMessage):
            for handler in self.on_waiting_done:
                handler[1](True, message_wrapper)

        elif isinstance(message_wrapper.message, QueryDHTMessage):
            self.engine.handle_query(message_wrapper)

    def __send(self):
        if not self.can_send():
            return

        message_wrapper = self.to_send_messages.pop(0)
        message_wrapper.send_at = current_time()
        if message_wrapper.message.message_type == b'q':
            message_wrapper.message.transaction_id = TransactionIdManager.next_trans_id()
        try:
            self.socket.sendto(message_wrapper.message.to_bytes(), (message_wrapper.node.ip, message_wrapper.node.port))
        except OSError:
            for handler in self.on_waiting_done:
                handler[1](False, message_wrapper)
            return

        self.last_send = current_time()
        if isinstance(message_wrapper.message, QueryDHTMessage):
            self.pending_messages.append(message_wrapper)

    def send(self, msg, node):
        message_wrapper = MessageWrapper(msg, node)
        self.to_send_messages.append(message_wrapper)

    def __check_outstanding(self):
        for waiting in list(self.pending_messages):
            if current_time() - waiting.send_at > 15000:
                self.pending_messages.remove(waiting)

                for handler in self.on_waiting_done:
                    handler[1](False, waiting)

    def stop(self):
        self.running = True
        self.socket.close()


class MessageWrapper:

    def __init__(self, message, node):
        self.send_at = 0
        self.message = message
        self.node = node
