import os

import time

from MediaPlayer.DHT2.Messages import QueryDHTMessage
from MediaPlayer.DHT2.Socket import Socket
from MediaPlayer.DHT2.Table import Table
from Shared.Logger import Logger
from Shared.Util import Singleton


class DHTEngine(metaclass=Singleton):

    def __init__(self):
        self.own_bytes = os.urandom(20)
        self.routing_table = Table(int(self.own_bytes.hex(), 16), [])
        self.socket = Socket(50000)

    def initialize(self):
        self.socket.start()
        request = QueryDHTMessage.create_find_node(self.own_bytes, self.own_bytes)
        self.socket.send_message(request, "r", self.routing_table.buckets[0].nodes[0].ip, self.routing_table.buckets[0].nodes[0].port, self.initialize_response, self.initialize_timeout)

    def initialize_response(self, data):
        Logger.write(2, "Initialize got a response: " + str(data))

    def initialize_timeout(self):
        Logger.write(2, "Initialize timed out")