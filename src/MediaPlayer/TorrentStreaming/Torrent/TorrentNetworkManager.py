import select
from time import sleep

from MediaPlayer.Util.Counter import AverageCounter
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

        self.last_inputs = 0
        self.last_outputs = 0

        self.throttling = False
        self.last_throttle = 0
        self.speed_log = 0

        self.average_download_counter = AverageCounter(self, 3)

        self.thread = None
        self._event_id_log = EventManager.register_event(EventType.Log, self.log)
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def log(self):
        Logger().write(LogVerbosity.Important, "-- TorrentNetworkManager state --")
        Logger().write(LogVerbosity.Important, "     Network manager: last run input sockets: " + str(self.last_inputs) + ", output: " + str(self.last_outputs))

    def unregister(self):
        EventManager.deregister_event(self._event_id_stopped)
        EventManager.deregister_event(self._event_id_log)

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
            input_peers, output_peers = self.torrent.peer_manager.get_peers_for_io()

            if not input_peers and not output_peers:
                sleep(0.05)  # no peers to read/write
                continue

            input_sockets = [x.connection_manager.connection.socket for x in input_peers]
            output_sockets = [x.connection_manager.connection.socket for x in output_peers]

            if not input_sockets and not output_sockets:
                sleep(0.01)  # no sockets available to read/write
                continue

            self.last_inputs = len(input_sockets)
            self.last_outputs = len(output_sockets)

            try:
                # Check which ones can read/write
                readable, writeable, exceptional = \
                    select.select(input_sockets, output_sockets, [], 0.2)
            except Exception as e:
                Logger().write(LogVerbosity.Important, "Select error: " + str(e))
                sleep(0.01)
                continue

            for client in readable:
                download_speed = self.average_download_counter.get_speed()
                if self.max_download_speed != 0 and download_speed > self.max_download_speed:
                    self.last_throttle = current_time()
                    if not self.throttling:
                        self.throttling = True
                        Logger().write(LogVerbosity.Debug, "Start throttling at " + str(self.max_download_speed))
                    sleep(0.05)
                    break

                peer = [x for x in input_peers if x.connection_manager.connection.socket == client]
                if len(peer) > 0:
                    peer = peer[0]
                    message = peer.connection_manager.handle_read()
                    if message is not None:
                        msg_length = len(message)
                        self.torrent.message_processor.add_message(peer, message, current_time())
                        self.average_download_counter.add_value(msg_length)

            for client in writeable:
                peer = [x for x in output_peers if x.connection_manager.connection.socket == client]
                if len(peer) > 0:
                    peer[0].connection_manager.handle_write()

            Timing().stop_timing("IO")
            sleep(0)

    def stop(self):
        self.running = False
        self.thread.join()
        self.torrent = None
