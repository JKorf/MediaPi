from MediaPlayer.Torrents.ExtensionManager import ProtocolExtensionManager
from MediaPlayer.Torrents.Peer.PeerMessages import BitfieldMessage, InterestedMessage, HandshakeMessage, ExtensionHandshakeMessage, \
    UninterestedMessage, MetadataMessage, HaveNoneMessage
from MediaPlayer.Util.Enums import ExtensionName, MetadataMessageType, TorrentState, PeerInterestedState, \
    PeerSpeed, PeerState
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import current_time


class PeerMetaDataManager(LogObject):

    def __init__(self, peer):
        super().__init__(peer, "meta")
        self.peer = peer

        self.handshake_send = False
        self.handshake_successful = False
        self.extension_handshake_send = False
        self.bitfield_done = False
        self.metadata_requested = False
        self.pause_handled = False
        self.port_send = False
        self.last_peer_exchange = current_time()

        self._low_peer_max_speed = Settings.get_int("low_peer_max_download_buffer") / 3
        self._medium_peer_max_speed = Settings.get_int("medium_peer_max_download_buffer") / 3

    def update(self):
        if self.peer.state != PeerState.Started:
            return True

        if not self.handshake_send:
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending handshake')
            self.handshake_send = True
            self.send_handshake()
            return True

        if not self.handshake_successful:
            if current_time() - self.peer.connection_manager.connected_on > 5000:
                self.peer.protocol_logger.update("No handshake response")
                # No handshake received
                self.peer.stop_async("No handshake")
                return False
            return True

        if not self.extension_handshake_send and self.peer.extension_manager.peer_supports(ExtensionName.ExtensionProtocol):
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' sending extended handshake')

            dic = ProtocolExtensionManager.create_extension_dictionary()
            handshake = ExtensionHandshakeMessage(dic)
            self.peer.protocol_logger.update("Sending extension handshake")
            self.peer.connection_manager.send(handshake.to_bytes())
            self.extension_handshake_send = True

        if self.peer.torrent.state == TorrentState.DownloadingMetaData:
            if self.metadata_requested:
                return True

            if self.peer.extension_manager.extension_dict is None:
                Logger().write(LogVerbosity.All, "Peer didn't receive extension handshake yet")
                return True

            if not self.peer.extension_manager.peer_supports(ExtensionName.Metadata):
                Logger().write(LogVerbosity.All, "Peer doesn't support metadata extension")
                return True

            self.metadata_requested = True

            Logger().write(LogVerbosity.Debug, str(self.peer.id) + " Requesting metadata")
            self.peer.protocol_logger.update("Sending metadata requests")
            to_request = self.peer.torrent.metadata_manager.get_pieces_to_do()
            for index in to_request:
                Logger().write(LogVerbosity.All, "Meta data request for piece " + str(index.index))
                self.peer.connection_manager.send(MetadataMessage(self.peer, MetadataMessageType.Request, index.index).to_bytes())

            return True

        if self.peer.torrent.state == TorrentState.WaitingUserFileSelection:
            return True

        if self.peer.torrent.state == TorrentState.Paused:
            if not self.pause_handled:
                self.pause_handled = True

                if self.peer.communication_state.out_interest == PeerInterestedState.Interested:
                    self.peer.protocol_logger.update("Sending uninterested (paused)")
                    Logger().write(LogVerbosity.Debug, "Paused, sending uninterested")
                    self.peer.communication_state.out_interest = PeerInterestedState.Uninterested
                    self.peer.connection_manager.send(UninterestedMessage().to_bytes())

            return True

        if not self.port_send:
            self.port_send = True
            # if self.peer.extension_manager.peer_supports(ExtensionName.DHT):
            #     Logger().write(LogVerbosity.All, str(self.peer.id) + ' sending port message')
            #     self.peer.connection_manager.send(PortMessage(Settings.get_int("dht_port")).to_bytes())

        if not self.peer.torrent.data_manager.bitfield:
            return False

        if not self.bitfield_done:
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending initial bitfield')
            self.bitfield_done = True
            if self.peer.extension_manager.peer_supports(ExtensionName.FastExtension) and \
               self.peer.torrent.data_manager.bitfield.has_none:
                    self.peer.protocol_logger.update("Sending HaveNone")
                    Logger().write(LogVerbosity.All, "Got nothing, sending HaveNone")
                    self.peer.connection_manager.send(HaveNoneMessage().to_bytes())
            else:
                Logger().write(LogVerbosity.All, "Sending bitfield message")
                self.peer.protocol_logger.update("Sending bitfield")
                self.peer.connection_manager.send(BitfieldMessage(self.peer.torrent.data_manager.bitfield.get_bitfield()).to_bytes())

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested and self.peer.download_manager.has_interesting_pieces():
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' Sending interested message')
            self.peer.protocol_logger.update("Sending interested")
            self.peer.communication_state.out_interest = PeerInterestedState.Interested
            self.peer.connection_manager.send(InterestedMessage().to_bytes())

        if self.peer.extension_manager.peer_supports(ExtensionName.PeerExchange):
            pass

        counter_value = self.peer.counter.value
        if counter_value < self._low_peer_max_speed:
            self.peer.peer_speed = PeerSpeed.Low
        elif counter_value < self._medium_peer_max_speed:
            self.peer.peer_speed = PeerSpeed.Medium
        else:
            self.peer.peer_speed = PeerSpeed.High

        return True

    def send_handshake(self):
        message = HandshakeMessage(self.peer.torrent.info_hash.sha1_hashed_bytes)
        message.reserved = ProtocolExtensionManager.add_extensions_to_handshake(message.reserved)

        Logger().write(LogVerbosity.All, "Sending handshake")
        self.peer.protocol_logger.update("Sending handshake")
        self.peer.connection_manager.send(message.to_bytes())

    def stop(self):
        self.peer = None