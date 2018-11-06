import os

import time
from random import Random

from MediaPlayer.DHT2.Node import Node, NodeState
from MediaPlayer.DHT2.Socket import Socket
from MediaPlayer.DHT2.Table import Table
from MediaPlayer.DHT2.Tasks import FindNodeTask
from MediaPlayer.Engine.Engine import Engine
from Shared.Logger import Logger
from Shared.Util import Singleton, current_time


class DHTEngine(metaclass=Singleton):

    def __init__(self):
        self.byte_id = None
        self.int_id = 0

        self.routing_table = Table(self)
        self.socket = Socket(50010, self.on_node_seen, self.on_node_timeout)
        self.engine = Engine("DHT Engine", 5000)
        self.engine.queue_repeating_work_item("DHT Refresh buckets", 1000 * 60, self.refresh_buckets)
        self.engine.queue_repeating_work_item("DHT Save nodes", 1000 * 60 * 5, self.save_nodes)

        self.running_tasks = []

    def on_node_seen(self, ip, port, id):
        if self.routing_table.contains_node(id):
            self.routing_table.update_node(id)
        else:
            self.routing_table.add_node(Node(ip, port, id))

    def on_node_timeout(self, ip, port):
        self.routing_table.fail_node(ip, port)

    def start(self):
        self.byte_id, nodes = self.load_nodes()
        if self.byte_id is None:
            self.byte_id = os.urandom(20)
        self.int_id = int(self.byte_id.hex(), 16)
        self.routing_table.init_nodes(nodes)

        self.socket.start()
        self.engine.start()
        self.start_task(FindNodeTask(self, self.byte_id, self.byte_id, self.routing_table.all_nodes()))

    def start_task(self, task, on_complete=None):
        task.on_complete = lambda: self.end_task(task, on_complete)
        self.running_tasks.append(task)
        task.execute()

    def end_task(self, task, on_complete):
        Logger.write(2, "DHT task " + task.__name__ + " completed in " + str(task.end_time - task.start_time) + "ms")
        self.running_tasks.remove(task)
        if on_complete:
            on_complete()

    def refresh_buckets(self):
        for bucket in list(self.routing_table.buckets):
            if current_time() - bucket.last_changed > 1000 * 60 * 15:
                self.start_task(FindNodeTask(self, self.byte_id, Random().randint(bucket.start, bucket.end), self.routing_table.all_nodes()))

    def save_nodes(self):
        all_nodes = self.byte_id
        for node in self.routing_table.all_nodes():
            if node.state != NodeState.Bad:
                all_nodes.extend(node.node_bytes())

        Logger.write(1, "DHT: Saving " + str(len(all_nodes) // 26) + " nodes")
        with open('dht.data', 'wb') as w:
            w.write(all_nodes)

    def load_nodes(self):
        try:
            with open("dht.data", "rb") as file:
                data = file.read()
            return data[0:20], Node.from_bytes_multiple(data[20:])
        except FileNotFoundError:
            return None, []

DHTEngine().start()

time.sleep(100)