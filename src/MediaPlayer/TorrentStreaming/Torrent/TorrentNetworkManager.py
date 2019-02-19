import select
from time import sleep

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Threading import CustomThread


class TorrentNetworkManager:

    def __init__(self, torrent):
        self.running = True

        self.torrent = torrent

        self.last_inputs = 0
        self.last_outputs = 0

        self.thread = None
        self.event_id_log = EventManager.register_event(EventType.Log, self.log)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def log(self):
        with Logger.lock:
            Logger.write(3, "-- TorrentNetworkManager state --")
            Logger.write(3, "     Network manager: last run input sockets: " + str(self.last_inputs) + ", output: " + str(self.last_outputs))

    def unregister(self):
        EventManager.deregister_event(self.event_id_stopped)
        EventManager.deregister_event(self.event_id_log)

    def start(self):
        Logger.write(2, "Starting network manager")
        self.thread = CustomThread(self.execute, "Torrent network thread")
        self.thread.start()

    def execute(self):
        while self.running:
            try:
                # Select in/outputs
                input_peers, output_peers = self.torrent.peer_manager.get_peers_for_io()

                if not input_peers and not output_peers:
                    sleep(0.05)
                    continue

                input_sockets = [x.connection_manager.connection.socket for x in input_peers]
                output_sockets = [x.connection_manager.connection.socket for x in output_peers]

                self.last_inputs = len(input_sockets)
                self.last_outputs = len(output_sockets)

                # Check which ones can read/write
                readable, writeable, exceptional = \
                    select.select(input_sockets, output_sockets, [], 0.2)
            except Exception as e:
                Logger.write(3, "Select error: " + str(e))
                continue

            for client in readable:
                [x for x in input_peers if x.connection_manager.connection.socket == client][0].connection_manager.on_readable()
            for client in writeable:
                [x for x in output_peers if x.connection_manager.connection.socket == client][0].connection_manager.on_writeable()

    def stop(self):
        self.running = False
        self.thread.join()
        self.torrent = None
