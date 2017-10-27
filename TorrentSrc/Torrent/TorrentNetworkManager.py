import select
from time import sleep

from Shared.Logger import Logger
from TorrentSrc.Util.Threading import CustomThread


class TorrentNetworkManager:

    def __init__(self, torrent):
        self.running = True

        self.torrent = torrent
        self.read_from = []
        self.write_to = []

    def start(self):
        Logger.write(2, "Starting network manager")
        thread = CustomThread(self.execute, "Torrent network thread")
        thread.start()

    def execute(self):
        while self.running:
            try:
                # Select in/outputs
                input = self.torrent.peer_manager.get_peers_for_receiving()
                output = self.torrent.peer_manager.get_peers_for_sending()

                if not input and not output:
                    sleep(0.05)
                    continue

                input_sockets = [x.connection_manager.connection.socket for x in input]
                output_sockets = [x.connection_manager.connection.socket for x in output]
                exceptional = []
                exceptional.extend(input_sockets)
                exceptional.extend(output_sockets)

                # Check which ones can read/write
                readable, writeable, exceptional = \
                    select.select(input_sockets, output_sockets, exceptional, 0.2)
            except Exception as e:
                Logger.write(3, "Select error: " + str(e))
                continue

            for client in readable:
                [x for x in input if x.connection_manager.connection.socket == client][0].connection_manager.handle_read()
            for client in writeable:
                [x for x in output if x.connection_manager.connection.socket == client][0].connection_manager.handle_write()
            for client in exceptional:
                Logger.write(2, "closing client because of exceptional")
                [x for x in input if x.connection_manager.connection.socket == client][0].connection_manager.disconnect()

    def stop(self):
        self.running = False

