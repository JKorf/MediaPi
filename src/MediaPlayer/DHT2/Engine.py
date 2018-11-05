import os

import time

from MediaPlayer.DHT2.Messages import QueryDHTMessage
from MediaPlayer.DHT2.Socket import Socket
from MediaPlayer.DHT2.Table import Table
from MediaPlayer.DHT2.Tasks import FindNodeTask
from Shared.Logger import Logger
from Shared.Util import Singleton


class DHTEngine(metaclass=Singleton):

    def __init__(self):
        self.own_bytes = os.urandom(20)
        self.routing_table = Table(int(self.own_bytes.hex(), 16), [])
        self.socket = Socket(50000)

    def initialize(self):
        self.socket.start()
        FindNodeTask(self, self.own_bytes, self.own_bytes, self.on_initialize_complete).execute()

    def on_initialize_complete(self):
        Logger.write(2, "Initialize task completed")

DHTEngine().initialize()

time.sleep(100)