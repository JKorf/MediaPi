from MediaPlayer.Torrents.Peer.PeerConnectionManager import PeerConnectionManager
from MediaPlayer.Torrents.Peer.PeerDownloadManager import PeerDownloadManager
from MediaPlayer.Torrents.Peer.PeerExtensionManager import PeerExtensionManager
from MediaPlayer.Torrents.Peer.PeerMetaDataManager import PeerMetaDataManager

from MediaPlayer.Torrents.Data import Bitfield
from MediaPlayer.Util.Counter import AverageCounter
from MediaPlayer.Util.Enums import PeerSpeed, PeerChokeState, PeerInterestedState, PeerSource, PeerState
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Stats import Stats
from Shared.Threading import CustomThread


class Peer(LogObject):
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

        CustomThread(self.connection_manager.start, "Start peer " + str(self.id)).start()

        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer started')

    def update(self):
        self.metadata_manager.update()
        self.download_manager.update()

    def on_connect(self):
        self.add_connected_peer_stat(self.source)

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

    def stop_async(self):
        if self.state != PeerState.Started and self.state != PeerState.Starting:
            return

        self.state = PeerState.Stopping
        CustomThread(self.stop, "Peer stopper " + str(self.id), []).start()

    def stop(self):
        self.state = PeerState.Stopping

        Logger().write(LogVerbosity.All, str(self.id) + ' Peer stopping')
        self.download_manager.stop()
        self.connection_manager.disconnect()

        self.state = PeerState.Stopped
        self.torrent = None
        self.finish()
        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer stopped')


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
