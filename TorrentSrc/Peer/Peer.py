from Shared.Logger import *
from Shared.Util import current_time
from TorrentSrc.Data import Bitfield
from TorrentSrc.Engine import Engine
from TorrentSrc.Peer.PeerConnectionManager import PeerConnectionManager
from TorrentSrc.Peer.PeerDownloadManager import PeerDownloadManager
from TorrentSrc.Peer.PeerExtensionManager import PeerExtensionManager
from TorrentSrc.Peer.PeerMessageHandler import PeerMessageHandler
from TorrentSrc.Peer.PeerMetaDataManager import PeerMetaDataManager
from TorrentSrc.Util.Counter import Counter
from TorrentSrc.Util.Enums import PeerSpeed, TorrentState, PeerChokeState, PeerInterestedState
from TorrentSrc.Util.Util import write_size


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

    def start(self):
        Logger.write(1, str(self.id) + ' Starting peer')
        self.running = True

        self.connection_manager = PeerConnectionManager(self, self.uri)
        self.download_manager = PeerDownloadManager(self)
        self.metadata_manager = PeerMetaDataManager(self)
        self.message_handler = PeerMessageHandler(self)
        self.extension_manager = PeerExtensionManager(self)
        self.counter = Counter()

        self.engine.queue_repeating_work_item("connection_manager", 30000, self.connection_manager.update)
        self.engine.queue_repeating_work_item("metadata_manager", 1000, self.metadata_manager.update)
        self.engine.queue_repeating_work_item("download_manager", 200, self.download_manager.update)
        self.engine.queue_repeating_work_item("peer_counter", 1000, self.counter.update)

        self.engine.start()
        Logger.write(1, str(self.id) + ' Peer started')

    def log(self):
        Logger.write(3, "     " + str(self.id) + " | " + self.communication_state.print() + " | " + str(self.peer_speed) +
                     "(" + write_size(self.counter.value) + ")" + " | Outstanding: " + str(
                         len(self.download_manager.downloading)))

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
