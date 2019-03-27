import time

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import ChokeMessage, BasePeerMessage, UnchokeMessage, InterestedMessage, \
    UninterestedMessage, HaveMessage, RequestMessage, PieceMessage, CancelMessage, PortMessage, BitfieldMessage, \
    ExtensionHandshakeMessage, PeerExchangeMessage, MetadataMessage, KeepAliveMessage, HaveAllMessage, HaveNoneMessage, \
    AllowedFastMessage, SuggestPieceMessage, RejectRequestMessage, HandshakeMessage
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import ConnectionState, PeerSource, PeerChokeState, PeerInterestedState, MetadataMessageType
from MediaPlayer.Util.MultiQueue import MultiQueue
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Timing import Timing


class TorrentMessageProcessor(LogObject):

    def __init__(self, torrent):
        super().__init__(torrent, "message processor")

        self.torrent = torrent
        self.metadata_wait_list = []

        self.queue = MultiQueue("Message queue", self.process_messages)

        # Logging props
        self.metadata_wait_list_log = 0
        self.message_queue_length = 0

    def start(self):
        self.queue.start()

    def stop(self):
        self.queue.stop()

    def add_message(self, peer, message, timestamp):
        self.queue.add_item((peer, message, timestamp))
        self.message_queue_length = len(self.queue.queue)

    def process_messages(self, messages):
        Timing().start_timing("process_messages")
        self.message_queue_length = len(self.queue.queue)
        if not self.torrent.is_preparing and len(self.metadata_wait_list) > 0:
            for peer, message, timestamp in self.metadata_wait_list:
                self.handle_message(peer, message, timestamp)
            self.metadata_wait_list.clear()
            self.metadata_wait_list_log = 0

        for peer, message_bytes, timestamp in messages:
            if not peer.metadata_manager.handshake_successful:
                # Handshake is the first message we should receive
                handshake = HandshakeMessage.from_bytes(message_bytes)
                if handshake is None:
                    Logger().write(LogVerbosity.All, str(peer.id) + ' invalid handshake response')
                    peer.stop_async()
                    continue

                if handshake.protocol != b'BitTorrent protocol':
                    Logger().write(LogVerbosity.Debug, 'Unknown bittorrent protocol, disconnecting. ' + str(handshake.protocol))
                    peer.stop_async()
                    continue

                peer.extension_manager.parse_extension_bytes(handshake.reserved)
                peer.metadata_manager.handshake_successful = True
                continue

            message = BasePeerMessage.from_bytes(message_bytes)
            if message is None:
                Logger().write(LogVerbosity.Info, "Unknown or invalid peer message received (id = " + str(message_bytes[0]) + "), closing connection")
                peer.stop_async()
                continue

            if self.torrent.is_preparing:
                # Add messages we cannot process yet to wait list
                if not isinstance(message, MetadataMessage) and not isinstance(message, ExtensionHandshakeMessage):
                    Logger().write(LogVerbosity.All, str(peer.id) + " Adding " + str(message.__class__.__name__) + " to metadata wait list")
                    self.metadata_wait_list.append((peer, message, timestamp))
                    self.metadata_wait_list_log = len(self.metadata_wait_list)
                    continue

            self.handle_message(peer, message, timestamp)
        Timing().stop_timing("process_messages")

    def handle_message(self, peer, message, timestamp):
        if isinstance(message, PieceMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received piece message: ' + str(message.index) + ', offset ' + str(message.offset))
            self.torrent.data_manager.block_done(peer, message.index, message.offset, message.data, timestamp)
            peer.counter.add_value(message.length)
            return

        elif isinstance(message, KeepAliveMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received keep alive message')
            return

        elif isinstance(message, ChokeMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received choke message')
            peer.communication_state.in_choke = PeerChokeState.Choked
            return

        elif isinstance(message, UnchokeMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received unchoke message')
            peer.communication_state.in_choke = PeerChokeState.Unchoked
            return

        elif isinstance(message, InterestedMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received interested message')
            peer.communication_state.in_interested = PeerInterestedState.Interested
            return

        elif isinstance(message, UninterestedMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received uninterested message')
            peer.communication_state.in_interested = PeerInterestedState.Uninterested
            return

        elif isinstance(message, HaveMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.All, str(peer.id) + ' Received have message')
                peer.bitfield.update_piece(message.piece_index, True)
            return

        elif isinstance(message, BitfieldMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.All, str(peer.id) + ' Received bitfield message')
                peer.bitfield.update(message.bitfield)
            return

        elif isinstance(message, RequestMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received request message')
            return

        elif isinstance(message, CancelMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received cancel message')
            return

        elif isinstance(message, PortMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received port message, port = ' + str(message.port))
            EventManager.throw_event(EventType.NewDHTNode, [peer.connection_manager.uri.hostname, message.port])
            return

        elif isinstance(message, HaveAllMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received HaveAll message")
                peer.bitfield.set_has_all()
            return

        elif isinstance(message, HaveNoneMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received HaveNone message")
                peer.bitfield.set_has_none()
            return

        elif isinstance(message, AllowedFastMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received AllowedFast message")
                peer.allowed_fast_pieces.append(message.piece_index)
            return

        elif isinstance(message, SuggestPieceMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + " Received SuggestPiece message")
            return

        elif isinstance(message, RejectRequestMessage):
            if peer.connection_state == ConnectionState.Connected:
                Logger().write(LogVerbosity.Debug, str(peer.id) + " Received RejectRequest message")
                peer.download_manager.request_rejected(message.index, message.offset, message.data_length)
            return

        elif isinstance(message, ExtensionHandshakeMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received extension handshake message')

            try:
                dic = Bencode.bdecode(message.bencoded_payload)
            except BTFailure:
                Logger().write(LogVerbosity.Debug, "Invalid extension handshake received")
                peer.stop_async()
                return

            peer.extension_manager.parse_dictionary(dic)
            if b'metadata_size' in dic:
                if peer is not None:
                    self.torrent.metadata_manager.set_total_size(dic[b'metadata_size'])

            return

        elif isinstance(message, PeerExchangeMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received ' + str(len(message.added)) + ' peers from peer exchange')
            self.torrent.peer_manager.add_potential_peers(message.added, PeerSource.PeerExchange)
            return

        elif isinstance(message, MetadataMessage):
            if message.metadata_message_type == MetadataMessageType.Data:
                Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received metadata message index ' + str(message.piece_index))
                self.torrent.metadata_manager.add_metadata_piece(message.piece_index, message.data)
            else:
                Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received metadata reject message ' + str(message.piece_index))
            return
