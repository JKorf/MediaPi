from socket import socket, AF_INET, SOCK_DGRAM

import time

from MediaPlayer.DHT2.Messages import NodeMessage, BaseDHTMessage, PendingMessage
from Shared.Logger import Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Socket:

    def __init__(self, port):
        self.port = port
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.settimeout(0.1)
        self.message_thread = CustomThread(self.message_thread_action, "DHT message thread", [])
        self.running = False

        self.last_send = 0
        self.received_messages = []
        self.to_send_messages = []
        self.awaiting_messages = []

    def start(self):
        self.socket.bind(('0.0.0.0', self.port))

        self.running = True
        self.message_thread.start()

    def send_message(self, msg, expecting_response_type, ip, port, on_response, on_timeout):
        self.to_send_messages.append(PendingMessage(NodeMessage(ip, port, msg), expecting_response_type, 0, on_response, on_timeout))

    def message_thread_action(self):
        Logger.write(2, "Starting DHT socket")
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

                msg = NodeMessage(sender[0], sender[1], msg_object)
                self.received_messages.append(msg)
                Logger.write(1, "Received DHT message")
        except OSError as e:
            return

    def send(self):
        for pending in list(self.to_send_messages):
            try:
                data = pending.message.message.to_bytes()
                self.socket.sendto(data, (pending.message.ip, pending.message.port))
                pending.send_at = current_time()
                self.awaiting_messages.append(pending)
                self.to_send_messages.remove(pending)
                Logger.write(1, "Sent DHT message")
            except OSError as e:
                Logger.write(1, "Failed to send: " + str(e))

    def check(self):
        for pending in list(self.awaiting_messages):
            if current_time() - pending.send_at > 10000:
                Logger.write(1, "DHT message timeout")
                pending.on_timeout()
                self.awaiting_messages.remove(pending)

        for received in list(self.received_messages):
            pending = [x for x in self.awaiting_messages if x.message.ip == received.ip and x.message.port == received.port and received.message.message_type == x.expecting_response_type]
            if len(pending) == 0:
                Logger.write(1, "DHT message request? No pending")
            elif len(pending) == 1:
                Logger.write(1, "DHT message response")
                pending[0].on_response(received.message) # answer to request
            else:
                Logger.write(1, "DHT message multiple pending?")

