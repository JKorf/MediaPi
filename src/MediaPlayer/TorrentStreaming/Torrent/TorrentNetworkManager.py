import select
from time import sleep

from MediaPlayer.Util.Counter import LiveCounter, AverageCounter
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import current_time


class TorrentNetworkManager:

    @property
    def max_download_speed(self):
        if self.torrent.bytes_ready_in_buffer > self.throttle_limit:
            return max(self.torrent.stream_speed, self.min_download_speed)
        else:
            return 0

    def __init__(self, torrent):
        self.running = True

        self.throttle_limit = Settings.get_int("start_throttling_buffer_size")
        self.min_download_speed = Settings.get_int("min_download_speed")
        self.torrent = torrent

        self.last_inputs = 0
        self.last_outputs = 0

        self.throttling = False
        self.last_throttle = 0

        self.live_download_counter = LiveCounter("Network speed live counter", 50)
        self.average_download_counter = AverageCounter("Network speed average counter", 3, 1000)

        self.thread = None
        self.event_id_log = EventManager.register_event(EventType.Log, self.log)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def log(self):
        Logger().write(LogVerbosity.Important, "-- TorrentNetworkManager state --")
        Logger().write(LogVerbosity.Important, "     Network manager: last run input sockets: " + str(self.last_inputs) + ", output: " + str(self.last_outputs))

    def unregister(self):
        EventManager.deregister_event(self.event_id_stopped)
        EventManager.deregister_event(self.event_id_log)

    def start(self):
        Logger().write(LogVerbosity.Info, "Starting network manager")
        self.live_download_counter.start()
        self.average_download_counter.start()
        self.thread = CustomThread(self.execute, "Torrent network thread")
        self.thread.start()

    def execute(self):
        while self.running:
            if self.throttling and current_time() - self.last_throttle > 2000:
                Logger().write(LogVerbosity.Debug, "No longer throttling")
                self.throttling = False # has not throttled in last 2 seconds

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
                Logger().write(LogVerbosity.Important, "Select error: " + str(e))
                continue

            for client in readable:
                download_speed = self.live_download_counter.value
                if self.max_download_speed != 0 and download_speed > self.max_download_speed:
                    self.last_throttle = current_time()
                    self.throttling = True
                    Logger().write(LogVerbosity.Debug, "Start throttling at " + str(self.max_download_speed))
                    sleep(0.05)
                    break

                peer = [x for x in input_peers if x.connection_manager.connection.socket == client]
                if len(peer) > 0:
                    bytes_read = peer[0].connection_manager.handle_read()
                    self.live_download_counter.add_value(bytes_read)
                    self.average_download_counter.add_value(bytes_read)

            for client in writeable:
                peer = [x for x in output_peers if x.connection_manager.connection.socket == client]
                if len(peer) > 0:
                    peer[0].connection_manager.handle_write()

    def stop(self):
        self.running = False
        self.thread.join()
        self.live_download_counter.stop()
        self.average_download_counter.stop()
        self.torrent = None
