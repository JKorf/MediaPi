from MediaPlayer.TorrentStreaming.Peer.PeerConnectionManager import PeerConnectionManager
from MediaPlayer.TorrentStreaming.Peer.PeerDownloadManager import PeerDownloadManager
from MediaPlayer.TorrentStreaming.Peer.PeerExtensionManager import PeerExtensionManager
from MediaPlayer.TorrentStreaming.Peer.PeerMetaDataManager import PeerMetaDataManager

from MediaPlayer.TorrentStreaming.Data import Bitfield
from MediaPlayer.TorrentStreaming.Peer.PeerMessageHandler import PeerMessageHandler
from MediaPlayer.Util.Counter import Counter
from MediaPlayer.Util.Enums import PeerSpeed, PeerChokeState, PeerInterestedState
from Shared import Engine
from Shared.Logger import *


class Peer:

    low_max_download_speed = 100000
    medium_max_download_speed = 250000

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
        Logger.write(1, str(self.id) + ' Starting peer')
        self.running = True

        self.connection_manager = PeerConnectionManager(self, self.uri)
        self.download_manager = PeerDownloadManager(self)
        self.metadata_manager = PeerMetaDataManager(self)
        self.message_handler = PeerMessageHandler(self)
        self.extension_manager = PeerExtensionManager(self)
        self.counter = Counter()

        self.engine.add_work_item("connection_manager", 30000, self.connection_manager.update)
        self.engine.add_work_item("metadata_manager", 1000, self.metadata_manager.update)
        self.engine.add_work_item("download_manager", 200, self.download_manager.update)
        self.engine.add_work_item("peer_counter", 1000, self.counter.update)

        self.engine.start()
        Logger.write(1, str(self.id) + ' Peer started')

    def log(self):
        Logger.write(3, "     " + str(self.id) + " | " + self.communication_state.print())

        self.connection_manager.log()
        self.download_manager.log()

    def stop(self):
        if not self.running:
            return

        Logger.write(1, str(self.id) + ' Peer stopping')
        self.running = False
        self.engine.stop()

        self.download_manager.stop()
        self.connection_manager.disconnect()
        Logger.write(1, str(self.id) + ' Peer stopped')


class PeerCommunicationState:

    def __init__(self):
        self.out_choke = PeerChokeState.Choked
        self.in_choke = PeerChokeState.Choked
        self.out_interest = PeerInterestedState.Uninterested
        self.in_interest = PeerInterestedState.Uninterested

    def print(self):
        return "Choke: Out " + str(self.out_choke) + ", In " + str(self.in_choke) + ", Interest: Out " + str(self.out_interest) + ", In " + str(self.in_interest)
