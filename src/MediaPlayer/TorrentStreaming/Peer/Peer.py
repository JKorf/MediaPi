from MediaPlayer.TorrentStreaming.Peer.PeerConnectionManager import PeerConnectionManager
from MediaPlayer.TorrentStreaming.Peer.PeerDownloadManager import PeerDownloadManager
from MediaPlayer.TorrentStreaming.Peer.PeerExtensionManager import PeerExtensionManager
from MediaPlayer.TorrentStreaming.Peer.PeerMetaDataManager import PeerMetaDataManager

from MediaPlayer.TorrentStreaming.Data import Bitfield
from MediaPlayer.TorrentStreaming.Peer.PeerMessageHandler import PeerMessageHandler
from MediaPlayer.Util.Counter import AverageCounter
from MediaPlayer.Util.Enums import PeerSpeed, PeerChokeState, PeerInterestedState, PeerSource
from Shared import Engine
from Shared.LogObject import LogObject, log_wrapper
from Shared.Logger import Logger, LogVerbosity
from Shared.Stats import Stats


class Peer(LogObject):
    @property
    def bitfield(self):
        # Only create a new bitfield when we actually have metadata for it
        if self.__bitfield is None and not self.torrent.is_preparing:
            self.__bitfield = Bitfield(self.torrent.data_manager.total_pieces)
        return self.__bitfield

    @property
    def connection_state(self):
        return self.connection_manager.connection_state

    def __init__(self, id, torrent, uri, source):
        super().__init__(torrent, "Peer " + str(id))
        self.id = id
        self.torrent = torrent
        self.uri = uri
        self.engine = Engine.Engine('Peer Engine', 200)
        self.running = False
        self.source = source

        self.connection_manager = None
        self.download_manager = None
        self.message_handler = None
        self.metadata_manager = None
        self.extension_manager = None

        self.__bitfield = None
        self.communication_state = PeerCommunicationState()
        self.counter = None
        self.peer_speed = PeerSpeed.Low

        self.allowed_fast_pieces = []

    def start(self):
        Logger().write(LogVerbosity.All, str(self.id) + ' Starting peer')
        self.running = True

        self.connection_manager = PeerConnectionManager(self, self.uri, self.on_connect, self.on_disconnect)
        self.download_manager = PeerDownloadManager(self)
        self.metadata_manager = PeerMetaDataManager(self)
        self.message_handler = PeerMessageHandler(self)
        self.extension_manager = PeerExtensionManager(self)
        self.counter = AverageCounter("Peerspeed counter", 3, 200)

        self.engine.add_work_item("connection_manager", 30000, self.connection_manager.update)
        self.engine.add_work_item("metadata_manager", 1000, self.metadata_manager.update)
        self.engine.add_work_item("download_manager", 200, self.download_manager.update)
        self.update_log("state", "connecting")

        self.counter.start()
        self.engine.start()
        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer started')

    def log(self):
        Logger().write(LogVerbosity.Important, "     " + str(self.id) + " | " + self.communication_state.print())

        self.connection_manager.log()
        self.download_manager.log()

    def on_connect(self):
        self.update_log("state", "connected")
        self.add_connected_peer_stat(self.source)

    def on_disconnect(self):
        self.stop()

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

    def stop(self):
        if not self.running:
            return

        self.update_log("state", "stopping")
        Logger().write(LogVerbosity.All, str(self.id) + ' Peer stopping')
        self.running = False

        self.engine.stop()
        self.message_handler.stop()
        self.metadata_manager.stop()
        self.download_manager.stop()
        self.connection_manager.disconnect()

        self.counter.stop()

        self.torrent = None
        self.update_log("state", "stopped")
        Logger().write(LogVerbosity.Debug, str(self.id) + ' Peer stopped')


class PeerCommunicationState:

    def __init__(self):
        self.out_choke = PeerChokeState.Choked
        self.in_choke = PeerChokeState.Choked
        self.out_interest = PeerInterestedState.Uninterested
        self.in_interest = PeerInterestedState.Uninterested

    def print(self):
        return "Choke: Out " + str(self.out_choke) + ", In " + str(self.in_choke) + ", Interest: Out " + str(self.out_interest) + ", In " + str(self.in_interest)
