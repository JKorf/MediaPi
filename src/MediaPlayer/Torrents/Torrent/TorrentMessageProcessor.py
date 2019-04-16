from time import sleep

from MediaPlayer.Torrents.Peer.PeerMessages import ChokeMessage, BasePeerMessage, UnchokeMessage, InterestedMessage, \
    UninterestedMessage, HaveMessage, RequestMessage, PieceMessage, CancelMessage, PortMessage, BitfieldMessage, \
    ExtensionHandshakeMessage, PeerExchangeMessage, MetadataMessage, KeepAliveMessage, HaveAllMessage, HaveNoneMessage, \
    AllowedFastMessage, SuggestPieceMessage, RejectRequestMessage, HandshakeMessage
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import PeerSource, PeerChokeState, PeerInterestedState, MetadataMessageType, PeerState
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Timing import Timing


class TorrentMessageProcessor(LogObject):

    def __init__(self, torrent):
        super().__init__(torrent, "message processor")

        self.torrent = torrent
        self.metadata_wait_list = []

        # Logging props
        self.metadata_wait_list_log = 0

    def process_messages(self, messages):
        Timing().start_timing("process_messages")
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
                    Logger().write(LogVerbosity.Debug, str(peer.id) + ' invalid handshake response')
                    peer.stop_async("Invalid handshake")
                    continue

                if handshake.protocol != b'BitTorrent protocol':
                    Logger().write(LogVerbosity.Debug, 'Unknown bittorrent protocol, disconnecting. ' + str(handshake.protocol))
                    peer.stop_async("Invalid protocol")
                    continue

                peer.protocol_logger.update("Received Handshake")
                peer.extension_manager.parse_extension_bytes(handshake.reserved)
                peer.metadata_manager.handshake_successful = True
                continue

            message = BasePeerMessage.from_bytes(message_bytes)
            if message is None:
                Logger().write(LogVerbosity.Info, "Unknown or invalid peer message received (id = " + str(message_bytes[0]) + "), closing connection")
                peer.stop_async("Unknown msg id")
                continue

            if self.torrent.is_preparing:
                # Add messages we cannot process yet to wait list
                if not isinstance(message, MetadataMessage) and not isinstance(message, ExtensionHandshakeMessage):
                    Logger().write(LogVerbosity.All, str(peer.id) + " Adding " + str(message.__class__.__name__) + " to metadata wait list")
                    self.metadata_wait_list.append((peer, message, timestamp))
                    self.metadata_wait_list_log = len(self.metadata_wait_list)
                    continue

            self.handle_message(peer, message, timestamp)
            sleep(0)
        Timing().stop_timing("process_messages")

    def handle_message(self, peer, message, timestamp):
        if isinstance(message, PieceMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received piece message: ' + str(message.index) + ', offset ' + str(message.offset))
            peer.protocol_logger.update("Sending/receiving requests", True)
            self.torrent.data_manager.block_done(peer, message.index, message.offset, message.data)
            peer.download_manager.block_done(message.index * self.torrent.data_manager.piece_length + message.offset, timestamp)
            peer.counter.add_value(message.length)
            return

        elif isinstance(message, KeepAliveMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received keep alive message')
            peer.protocol_logger.update("Received KeepAlive")
            return

        elif isinstance(message, ChokeMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received choke message')
            peer.protocol_logger.update("Received Choke")
            peer.communication_state.in_choke = PeerChokeState.Choked
            return

        elif isinstance(message, UnchokeMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received unchoke message')
            peer.protocol_logger.update("Received UnChoke")
            peer.communication_state.in_choke = PeerChokeState.Unchoked
            return

        elif isinstance(message, InterestedMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received interested message')
            peer.protocol_logger.update("Received Interested")
            peer.communication_state.in_interest = PeerInterestedState.Interested
            return

        elif isinstance(message, UninterestedMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received uninterested message')
            peer.protocol_logger.update("Received Uninterested")
            peer.communication_state.in_interest = PeerInterestedState.Uninterested
            return

        elif isinstance(message, HaveMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.All, str(peer.id) + ' Received have message')
                peer.protocol_logger.update("Received Have", True)
                peer.bitfield.update_piece(message.piece_index, True)
            return

        elif isinstance(message, BitfieldMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.All, str(peer.id) + ' Received bitfield message')
                peer.protocol_logger.update("Received Bitfield")
                peer.bitfield.update(message.bitfield)
            return

        elif isinstance(message, RequestMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received request message')
            peer.protocol_logger.update("Received Request")
            return

        elif isinstance(message, CancelMessage):
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received cancel message')
            peer.protocol_logger.update("Received Cancel")
            return

        elif isinstance(message, PortMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received port message, port = ' + str(message.port))
            peer.protocol_logger.update("Received Port")
            EventManager.throw_event(EventType.NewDHTNode, [peer.connection_manager.uri.hostname, message.port])
            return

        elif isinstance(message, HaveAllMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received HaveAll message")
                peer.protocol_logger.update("Received HaveAll")
                peer.bitfield.set_has_all()
            return

        elif isinstance(message, HaveNoneMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received HaveNone message")
                peer.protocol_logger.update("Received HaveNone")
                peer.bitfield.set_has_none()
            return

        elif isinstance(message, AllowedFastMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.All, str(peer.id) + " Received AllowedFast message")
                peer.protocol_logger.update("Received AllowedFast", True)
                peer.allowed_fast_pieces.append(message.piece_index)
            return

        elif isinstance(message, SuggestPieceMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + " Received SuggestPiece message")
            peer.protocol_logger.update("Received SuggestPiece", True)
            return

        elif isinstance(message, RejectRequestMessage):
            if peer.state == PeerState.Started:
                Logger().write(LogVerbosity.Debug, str(peer.id) + " Received RejectRequest message")
                peer.protocol_logger.update("Received RejectRequest", True)
                peer.download_manager.request_rejected(message.index, message.offset, message.data_length)
            return

        elif isinstance(message, ExtensionHandshakeMessage):
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received extension handshake message')
            peer.protocol_logger.update("Received ExtensionHandshake")

            try:
                dic = Bencode.bdecode(message.bencoded_payload)
            except BTFailure:
                Logger().write(LogVerbosity.Debug, "Invalid extension handshake received")
                peer.stop_async("Invalid extension handshake")
                return

            peer.extension_manager.parse_dictionary(dic)
            if b'metadata_size' in dic:
                if peer is not None:
                    self.torrent.metadata_manager.set_total_size(dic[b'metadata_size'])

            return

        elif isinstance(message, PeerExchangeMessage):
            peer.protocol_logger.update("Received PeerExchange")
            Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received ' + str(len(message.added)) + ' peers from peer exchange')
            self.torrent.peer_manager.add_potential_peers(message.added, PeerSource.PeerExchange)
            return

        elif isinstance(message, MetadataMessage):
            if message.metadata_message_type == MetadataMessageType.Data:
                peer.protocol_logger.update("Received Metadata")
                Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received metadata message index ' + str(message.piece_index))
                self.torrent.metadata_manager.add_metadata_piece(message.piece_index, message.data)
            else:
                peer.protocol_logger.update("Received Metadata rejected")
                Logger().write(LogVerbosity.Debug, str(peer.id) + ' Received metadata reject message ' + str(message.piece_index))
            return
