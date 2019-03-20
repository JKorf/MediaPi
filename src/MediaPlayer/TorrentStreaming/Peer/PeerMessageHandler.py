import time

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import ChokeMessage, BasePeerMessage, UnchokeMessage, InterestedMessage, \
    UninterestedMessage, HaveMessage, RequestMessage, PieceMessage, CancelMessage, PortMessage, BitfieldMessage, \
    ExtensionHandshakeMessage, PeerExchangeMessage, MetadataMessage, KeepAliveMessage, HaveAllMessage, HaveNoneMessage, \
    AllowedFastMessage, SuggestPieceMessage, RejectRequestMessage
from MediaPlayer.Util import Bencode
from MediaPlayer.Util.Bencode import BTFailure
from MediaPlayer.Util.Enums import ConnectionState, PeerSource, TorrentState, PeerChokeState, PeerInterestedState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import current_time


class PeerMessageHandler:

    def __init__(self, peer):
        self.peer = peer
        self.metadata_wait_list = []

    def update(self, allowed_process_time):
        if self.peer is None:
            # This peer is stopped stopped
            return True

        if self.peer.connection_state != ConnectionState.Connected\
        and self.peer.connection_state != ConnectionState.Disconnected:
            return True

        if not self.peer.metadata_manager.handshake_successful:
            return True

        processed_messages = 0
        start_time = current_time()
        while current_time() - start_time < allowed_process_time:
            if self.peer.torrent.state == TorrentState.Downloading and len(self.metadata_wait_list) > 0:
                # Process wait list
                Logger().write(LogVerbosity.Debug, str(self.peer.id) + " Processing already received messages now that we have metadata")
                for message in self.metadata_wait_list:
                    self.handle_message(message)

                self.metadata_wait_list.clear()

            msg_bytes = self.peer.connection_manager.get_message()
            if msg_bytes is None:
                # Nothing in buffer atm
                return True

            message = BasePeerMessage.from_bytes(self.peer, msg_bytes)
            if message is None:
                # Connection closed
                Logger().write(LogVerbosity.Info, "Unknown or invalid peer message received (id = " + str(msg_bytes[0]) + "), closing connection")
                self.peer.stop()
                return False

            if self.peer.torrent.is_preparing:
                # Add messages we cannot process yet to wait list
                if not isinstance(message, MetadataMessage) and not isinstance(message, ExtensionHandshakeMessage):
                    Logger().write(LogVerbosity.All, str(self.peer.id) + " Adding " + str(message.__class__.__name__) + " to metadata wait list")
                    self.metadata_wait_list.append(message)
                    continue

            # Handle messages
            self.handle_message(message)
            processed_messages += 1
            time.sleep(0)
        return True

    def handle_message(self, message):
        if isinstance(message, PieceMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Received piece message: ' + str(message.index) + ', offset ' + str(message.offset))
            self.peer.torrent.data_manager.block_done(self.peer, message.index, message.offset, message.data)
            self.peer.counter.add_value(message.length)
            return

        elif isinstance(message, KeepAliveMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received keep alive message')
            return

        elif isinstance(message, ChokeMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received choke message')
            self.peer.communication_state.in_choke = PeerChokeState.Choked
            return

        elif isinstance(message, UnchokeMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received unchoke message')
            self.peer.communication_state.in_choke = PeerChokeState.Unchoked
            return

        elif isinstance(message, InterestedMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received interested message')
            self.peer.communication_state.in_interested = PeerInterestedState.Interested
            return

        elif isinstance(message, UninterestedMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received uninterested message')
            self.peer.communication_state.in_interested = PeerInterestedState.Uninterested
            return

        elif isinstance(message, HaveMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Received have message')
            self.peer.bitfield.update_piece(message.piece_index, True)
            return

        elif isinstance(message, BitfieldMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Received bitfield message')
            self.peer.bitfield.update(message.bitfield)
            return

        elif isinstance(message, RequestMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received request message')
            return

        elif isinstance(message, CancelMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received cancel message')
            return

        elif isinstance(message, PortMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Received port message, port = ' + str(message.port))
            EventManager.throw_event(EventType.NewDHTNode, [self.peer.connection_manager.uri.hostname, message.port])
            return

        elif isinstance(message, HaveAllMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + " Received HaveAll message")
            self.peer.bitfield.set_has_all()
            return

        elif isinstance(message, HaveNoneMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + " Received HaveNone message")
            self.peer.bitfield.set_has_none()
            return

        elif isinstance(message, AllowedFastMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + " Received AllowedFast message")
            self.peer.allowed_fast_pieces.append(message.piece_index)
            return

        elif isinstance(message, SuggestPieceMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + " Received SuggestPiece message")
            return

        elif isinstance(message, RejectRequestMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + " Received RejectRequest message")
            self.peer.download_manager.request_rejected(message.index, message.offset, message.data_length)
            return

        elif isinstance(message, ExtensionHandshakeMessage):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Received extension handshake message')

            try:
                dic = Bencode.bdecode(message.bencoded_payload)
            except BTFailure:
                Logger().write(LogVerbosity.Debug, "Invalid extension handshake received")
                self.peer.stop()
                return

            self.peer.extension_manager.parse_dictionary(dic)
            if b'metadata_size' in dic:
                if self.peer is not None:
                    self.peer.torrent.metadata_manager.set_total_size(dic[b'metadata_size'])

            return

        elif isinstance(message, PeerExchangeMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received ' + str(len(message.added)) + ' peers from peer exchange')
            self.peer.torrent.peer_manager.add_potential_peers(message.added, PeerSource.PeerExchange)
            return

        elif isinstance(message, MetadataMessage):
            Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' Received metadata message index ' + str(message.piece_index))
            self.peer.torrent.metadata_manager.add_metadata_piece(message.piece_index, message.data)
            return

    def stop(self):
        self.peer = None