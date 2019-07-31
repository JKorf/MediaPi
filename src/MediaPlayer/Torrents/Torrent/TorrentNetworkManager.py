import select
from time import sleep

from MediaPlayer.Torrents.TorrentManager import TorrentManager
from MediaPlayer.Util.Counter import AverageCounter
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Timing import Timing
from Shared.Util import current_time


class TorrentNetworkManager(TorrentManager):

    def __init__(self, torrent):
        super().__init__(torrent, "network")

        self.running = True
        self.torrent = torrent

        self.speed_log = 0

        self.average_download_counter = AverageCounter(self, 3)

        self.thread = None
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def unregister(self):
        EventManager.deregister_event(self._event_id_stopped)

    def start(self):
        Logger().write(LogVerbosity.Info, "Starting network manager")
        self.thread = CustomThread(self.execute, "Network IO")
        self.thread.start()

    def execute(self):
        while self.running:
            Timing().start_timing("IO")
            # Select in/outputs
            input_peers = self.torrent.peer_manager.get_peers_for_reading()
            received_messages = []
            for peer in input_peers:
                messages_size, messages = peer.connection_manager.handle_read()
                if messages_size > 0:
                    self.average_download_counter.add_value(messages_size)
                    time = current_time()
                    received_messages += [(peer, x, time) for x in messages]

            if len(received_messages) != 0:
                self.torrent.message_processor.process_messages(received_messages)

            for peer in self.torrent.peer_manager.connected_peers:
                peer.download_manager.update_requests()

            output_peers = self.torrent.peer_manager.get_peers_for_writing()
            for peer in output_peers:
                peer.connection_manager.handle_write()

            Timing().stop_timing("IO")
            sleep(0.005)

    def stop(self):
        self.running = False
        self.thread.join()
        super().stop()
