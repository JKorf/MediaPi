import time

from MediaPlayer.Torrents.Peer.PeerConnectionManager import PeerConnectionManager
from MediaPlayer.Torrents.Peer.PeerDownloadManager import PeerDownloadManager
from MediaPlayer.Torrents.Peer.PeerExtensionManager import PeerExtensionManager
from MediaPlayer.Torrents.Peer.PeerMetaDataManager import PeerMetaDataManager

from MediaPlayer.Torrents.Data import Bitfield
from MediaPlayer.Torrents.TorrentManager import TorrentManager
from MediaPlayer.Util.Counter import AverageCounter
from MediaPlayer.Util.Enums import PeerSpeed, PeerChokeState, PeerInterestedState, PeerSource, PeerState
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Stats import Stats
from Shared.Threading import CustomThread
from Shared.Util import current_time


class Peer(TorrentManager):
    @property
    def bitfield(self):
        # Only create a new bitfield when we actually have metadata for it
        if self.__bitfield is None and not self.torrent.is_preparing:
            self.__bitfield = Bitfield(self, self.torrent.data_manager.total_pieces)
        return self.__bitfield

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state != value:
            old = self._state
            self._state = value
            if self.torrent.peer_manager is not None:
                self.torrent.peer_manager.update_peer(self, old, value)

            if value == PeerState.Started:
                self.peer_state_task = CustomThread(self.check_peer_state, "Check peer state " + str(self.id))
                self.peer_state_task.start()

    def __init__(self, id, torrent, uri, source):
        super().__init__(torrent, "Peer " + str(id))
        self.id = id
        self.torrent = torrent
        self.uri = uri
        self._state = PeerState.Initial
        self.source = source

        self.connection_manager = None
        self.download_manager = None
        self.metadata_manager = None
        self.extension_manager = None

        self.__bitfield = None
        self.communication_state = PeerCommunicationState(self)
        self.counter = None
        self.peer_speed = PeerSpeed.Low

        self.allowed_fast_pieces = []

        self.round_trips = 0
        self.round_trip_total = 0
        self.round_trip_average = 0
        self.max_blocks_log = 0
        self.speed_log = 0

        self.peer_start_task = None
        self.peer_state_task = None
        self.peer_stop_task = None

        self.stop_reason = "Torrent stopping"
        self.protocol_logger = ProtocolLogger(self)

    def adjust_round_trip_time(self, time):
        self.round_trips += 1
        self.round_trip_total += time
        self.round_trip_average = self.round_trip_total / self.round_trips

    def start(self):
        Logger().write(LogVerbosity.All, str(self.id) + ' Starting peer')
        self.state = PeerState.Starting

        self.connection_manager = PeerConnectionManager(self, self.uri)
        self.download_manager = PeerDownloadManager(self)
        self.metadata_manager = PeerMetaDataManager(self)
        self.extension_manager = PeerExtensionManager(self)
        self.counter = AverageCounter(self, 3)

        self.peer_start_task = CustomThread(self.connection_manager.start, "Start peer " + str(self.id))
        self.peer_start_task.start()

        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer started')

    def update(self):
        self.metadata_manager.update()
        self.download_manager.update()

    def check_peer_state(self):
        zero_speed_checks = 0
        while self.state == PeerState.Started:
            if current_time() - self.connection_manager.connected_on < 20000:
                time.sleep(1)
                continue

            if not self.torrent.peer_manager.should_stop_peers():
                time.sleep(1)
                continue

            if self.counter.total == 0:
                Logger().write(LogVerbosity.Info, str(self.id) + " stopping not downloading peer")
                self.stop_async("Not downloading")  # Stop since we haven't downloaded anything since connecting
                return

            if self.counter.value == 0:
                zero_speed_checks += 1
                if zero_speed_checks >= 10:
                    Logger().write(LogVerbosity.Info,  str(self.id) + " stopping currently not downloading peer")
                    self.stop_async("Not recently downloading")  # Stop since we haven't downloaded anything in the last 10 seconds
                    return
            else:
                zero_speed_checks = 0

            time.sleep(1)

    @staticmethod
    def add_connected_peer_stat(source):
        if source == PeerSource.DHT:
            Stats.add('peers_source_dht_connected', 1)
        elif source == PeerSource.HttpTracker:
            Stats.add('peers_source_http_tracker_connected', 1)
        elif source == PeerSource.UdpTracker:
            Stats.add('peers_source_udp_tracker_connected', 1)
        elif source == PeerSource.PeerExchange:
            Stats.add('peers_source_exchange_connected', 1)

    def stop_async(self, reason):
        if self.state != PeerState.Started and self.state != PeerState.Starting:
            return

        self.stop_reason = reason
        self.state = PeerState.Stopping
        self.peer_stop_task = CustomThread(self.stop, "Peer stopper " + str(self.id), [])
        self.peer_stop_task.start()

    def stop(self):
        self.state = PeerState.Stopping
        Logger().write(LogVerbosity.All, str(self.id) + ' Peer stopping')
        if self.peer_state_task is not None:
            self.peer_state_task.join()

        self.download_manager.stop()
        self.connection_manager.disconnect()
        self.extension_manager.stop()
        self.metadata_manager.stop()

        self.state = PeerState.Stopped
        self.peer_start_task.join()

        self.protocol_logger = None
        super().stop()
        self.finish()
        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer stopped: ' + self.stop_reason)


class PeerCommunicationState(LogObject):

    def __init__(self, peer):
        super().__init__(peer, "com state")

        self.out_choke = PeerChokeState.Choked
        self.in_choke = PeerChokeState.Choked
        self.out_interest = PeerInterestedState.Uninterested
        self.in_interest = PeerInterestedState.Uninterested

    def print(self):
        return "Choke: Out " + str(self.out_choke) + ", In " + str(self.in_choke) + ", Interest: Out " + str(self.out_interest) + ", In " + str(self.in_interest)


class ProtocolLogger(LogObject):

    def __init__(self, peer):
        super().__init__(peer, "protocol")
        self.children = []
        self.cache = 0
        self.current_cache = None

    def update(self, step, aggregate=False):
        if self.current_cache is not None and self.current_cache != step:
            # process cache
            prot = LogObject(self, self.current_cache + " x" + str(self.cache))
            self.children.append(prot)
            self.cache = 0
            self.current_cache = None

        if aggregate:
            self.current_cache = step
            self.cache += 1
            return

        prot = LogObject(self, step)
        self.children.append(prot)
