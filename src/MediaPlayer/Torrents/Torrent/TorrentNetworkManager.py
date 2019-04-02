import select
from time import sleep

from MediaPlayer.Util.Counter import AverageCounter
from MediaPlayer.Util.Enums import PeerState
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Timing import Timing
from Shared.Util import current_time


class TorrentNetworkManager(LogObject):

    @property
    def max_download_speed(self):
        if self.torrent.bytes_ready_in_buffer > self.throttle_limit:
            return max(self.torrent.stream_speed, self.min_download_speed)
        else:
            return 0

    def __init__(self, torrent):
        super().__init__(torrent, "network")

        self.running = True

        self.throttle_limit = Settings.get_int("start_throttling_buffer_size")
        self.min_download_speed = Settings.get_int("min_download_speed")
        self.torrent = torrent

        self.throttling = False
        self.last_throttle = 0
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
            if self.throttling and current_time() - self.last_throttle > 2000:
                Logger().write(LogVerbosity.Debug, "No longer throttling")
                self.throttling = False  # has not throttled in last 2 seconds

            # Select in/outputs
            input_peers = self.torrent.peer_manager.get_peers_for_reading()
            # if len(input_peers) == 0 and len(output_peers) == 0:
            #     sleep(0.01)
            #     continue

            received_messages = []
            for peer in input_peers:
                download_speed = self.average_download_counter.get_speed()
                if self.max_download_speed != 0 and download_speed > self.max_download_speed:
                    self.last_throttle = current_time()
                    if not self.throttling:
                        self.throttling = True
                        Logger().write(LogVerbosity.Debug, "Start throttling at " + str(self.max_download_speed))
                    sleep(0.05)
                    break

                messages_size, messages = peer.connection_manager.handle_read()
                if messages_size > 0:
                    self.average_download_counter.add_value(messages_size)
                    time = current_time()
                    received_messages += [(peer, x, time) for x in messages]

            if len(received_messages) != 0:
                self.torrent.message_processor.process_messages(received_messages)

            for peer in [peer for peer, msg, time in received_messages if peer.state == PeerState.Started]:
                peer.download_manager.update_requests()

            output_peers = self.torrent.peer_manager.get_peers_for_writing()
            for peer in output_peers:
                peer.connection_manager.handle_write()

            Timing().stop_timing("IO")
            sleep(0.005)

    def stop(self):
        self.running = False
        self.thread.join()
        self.torrent = None
