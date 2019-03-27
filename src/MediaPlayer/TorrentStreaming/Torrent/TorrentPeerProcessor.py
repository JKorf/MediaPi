import time

from Shared.Threading import CustomThread
from Shared.Util import current_time


class TorrentPeerProcessor:

    def __init__(self, torrent):
        self.torrent = torrent

        self.running = False
        self.process_thread = CustomThread(self.process, "Peer processor")

    def start(self):
        self.running = True
        self.process_thread.start()

    def stop(self):
        self.running = False
        self.process_thread.join()

    def process(self):
        while self.running:
            start_time = current_time()
            peers_to_process = list(self.torrent.peer_manager.connected_peers)

            for peer in peers_to_process:
                peer.update()

            time.sleep(100 - current_time() - start_time)
