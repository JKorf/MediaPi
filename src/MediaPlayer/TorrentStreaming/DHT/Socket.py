import time
from socket import socket, AF_INET, SOCK_DGRAM

from MediaPlayer.TorrentStreaming.DHT.Messages import NodeMessage, BaseDHTMessage, QueryMessage, ErrorDHTMessage, QueryDHTMessage, ResponseDHTMessage
from Shared.Logger import Logger, LogVerbosity
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Socket:

    def __init__(self, port, on_node_seen, on_node_timeout, on_query):
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.settimeout(0.1)
        self.message_thread = CustomThread(self.message_thread_action, "DHT message thread", [])
        self.running = False

        self.node_seen_handler = on_node_seen
        self.node_timeout_handler = on_node_timeout
        self.query_handler = on_query

        self.last_send = 0
        self.received_messages = []
        self.to_send_messages = []
        self.awaiting_messages = []

    def start(self):
        self.socket.bind(('0.0.0.0', self.port))

        self.running = True
        self.message_thread.start()

    def send_response(self, msg, ip, port):
        self.to_send_messages.append(NodeMessage(ip, port, msg))

    def send_query(self, msg, ip, port, on_response, on_timeout):
        self.to_send_messages.append(QueryMessage(NodeMessage(ip, port, msg), 0, on_response, on_timeout))

    def message_thread_action(self):
        Logger().write(LogVerbosity.Debug, "Starting DHT socket")
        while self.running:
            self.receive()
            self.send()
            self.check()
            time.sleep(0.005)

    def receive(self):
        try:
            while True:
                data, sender = self.socket.recvfrom(2048)
                msg_object = BaseDHTMessage.from_bytes(data)
                if msg_object is None:
                    return

                if isinstance(msg_object, ErrorDHTMessage):
                    Logger().write(LogVerbosity.Debug, "DHT error message: " + str(msg_object.errorcode) + " " + str(msg_object.errormsg))
                    continue
                else:
                    self.node_seen_handler(sender[0], sender[1], msg_object.id)

                msg = NodeMessage(sender[0], sender[1], msg_object)
                self.received_messages.append(msg)
                Logger().write(LogVerbosity.All, "Received DHT message")
        except OSError as e:
            return

    def send(self):
        for pending in list(self.to_send_messages):
            try:
                if not isinstance(pending, QueryMessage):
                    data = pending.message.to_bytes()
                    self.socket.sendto(data, (pending.ip, pending.port))
                    self.to_send_messages.remove(pending)
                    Logger().write(LogVerbosity.All, "Sent DHT response")
                else:
                    data = pending.message.message.to_bytes()
                    self.socket.sendto(data, (pending.message.ip, pending.message.port))
                    pending.send_at = current_time()
                    self.awaiting_messages.append(pending)
                    self.to_send_messages.remove(pending)
                    Logger().write(LogVerbosity.All, "Sent DHT query")
            except OSError as e:
                Logger().write(LogVerbosity.All, "Failed to send: " + str(e))

    def check(self):
        for pending in list(self.awaiting_messages):
            if current_time() - pending.send_at > 10000:
                Logger().write(LogVerbosity.All, "DHT message timeout")
                self.node_timeout_handler(pending.message.ip, pending.message.port)
                pending.on_timeout()
                self.awaiting_messages.remove(pending)

        for received in list(self.received_messages):
            if isinstance(received.message, QueryDHTMessage):
                self.query_handler(received.ip, received.port, received.message)
                self.received_messages.remove(received)
                continue

            elif isinstance(received.message, ResponseDHTMessage):
                pending = [x for x in self.awaiting_messages if x.message.message.transaction_id == received.message.transaction_id]
                if len(pending) == 0:
                    Logger().write(LogVerbosity.All, "DHT response for no request (timed out?)")
                    self.received_messages.remove(received)
                    continue

                Logger().write(LogVerbosity.All, "DHT message response")
                pending[0].on_response(received.message)  # answer to request
                self.received_messages.remove(received)
                self.awaiting_messages.remove(pending[0])

