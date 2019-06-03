import time

from MediaPlayer.Torrents.TorrentManager import TorrentManager
from Shared.Threading import CustomThread
from Shared.Timing import Timing
from Shared.Util import current_time


class TorrentPeerProcessor(TorrentManager):

    def __init__(self, torrent):
        TorrentManager.__init__(self, torrent, "Peer processor")

        self.running = False
        self.process_thread = CustomThread(self.process, "Peer processor")

    def start(self):
        self.running = True
        self.process_thread.start()

    def stop(self):
        self.running = False
        self.process_thread.join()
        super().stop()

    def process(self):
        while self.running:
            start_time = current_time()
            peers_to_process = self.torrent.peer_manager.connected_peers

            Timing().start_timing("peer_processing")
            for peer in peers_to_process:
                peer.metadata_manager.update()
                peer.download_manager.update_timeout()
            Timing().stop_timing("peer_processing")

            spend_time = current_time() - start_time
            time.sleep(0.1 - (spend_time / 1000))
