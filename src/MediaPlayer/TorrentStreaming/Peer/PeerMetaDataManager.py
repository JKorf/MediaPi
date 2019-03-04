from time import sleep

from MediaPlayer.TorrentStreaming.ExtensionManager import ProtocolExtensionManager
from MediaPlayer.TorrentStreaming.Peer.PeerMessages import BitfieldMessage, InterestedMessage, HandshakeMessage, ExtensionHandshakeMessage, \
    UninterestedMessage, MetadataMessage, PortMessage, HaveNoneMessage
from MediaPlayer.Util.Enums import ConnectionState, ExtensionName, MetadataMessageType, TorrentState, PeerInterestedState, \
    PeerSpeed
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time


class PeerMetaDataManager:

    def __init__(self, peer):
        self.peer = peer

        self.handshake_done = False
        self.handshake_successful = False
        self.bitfield_done = False
        self.metadata_requested = False
        self.pause_handled = False
        self.port_send = False
        self.last_peer_exchange = current_time()

    def update(self):
        if self.peer.connection_manager.connection_state != ConnectionState.Connected:
            return True

        if not self.handshake_done:
            Logger().write(1, str(self.peer.id) + ' Sending handshake')
            self.handshake_done = True
            if not self.handshake():
                self.peer.stop()
                return False

            if self.peer.extension_manager.peer_supports(ExtensionName.ExtensionProtocol):
                Logger().write(1, str(self.peer.id) + ' sending extended handshake')

                dic = ProtocolExtensionManager.create_extension_dictionary()
                handshake = ExtensionHandshakeMessage(dic)
                Logger().write(1, "Sending extension handshake")
                self.peer.connection_manager.send(handshake.to_bytes())

        if self.peer.torrent.state == TorrentState.DownloadingMetaData:
            if self.metadata_requested:
                return True

            if self.peer.extension_manager.extension_dict is None:
                Logger().write(1, "Peer didn't receive extension handshake yet")
                return True

            if not self.peer.extension_manager.peer_supports(ExtensionName.Metadata):
                Logger().write(1, "Peer doesn't support metadata extension")
                return True

            self.metadata_requested = True

            Logger().write(2, str(self.peer.id) + " Requesting metadata")

            to_request = self.peer.torrent.metadata_manager.get_pieces_to_do()
            for index in to_request:
                Logger().write(1, "Meta data request for piece " + str(index.index))
                self.peer.connection_manager.send(MetadataMessage(self.peer, MetadataMessageType.Request, index.index).to_bytes())

            return True

        if self.peer.torrent.state == TorrentState.WaitingUserFileSelection:
            return True

        if self.peer.torrent.state == TorrentState.Paused:
            if not self.pause_handled:
                self.pause_handled = True

                if self.peer.communication_state.out_interest == PeerInterestedState.Interested:
                    Logger().write(1, "Paused, sending uninterested")
                    self.peer.communication_state.out_interest = PeerInterestedState.Uninterested
                    self.peer.connection_manager.send(UninterestedMessage().to_bytes())

            return True

        if not self.port_send:
            self.port_send = True
            if self.peer.extension_manager.peer_supports(ExtensionName.DHT):
                Logger().write(1, str(self.peer.id) + ' sending port message')
                self.peer.connection_manager.send(PortMessage(Settings.get_int("dht_port")).to_bytes())

        if not self.peer.torrent.data_manager.bitfield:
            return False

        if not self.bitfield_done:
            Logger().write(1, str(self.peer.id) + ' Sending initial bitfield')
            self.bitfield_done = True
            if self.peer.extension_manager.peer_supports(ExtensionName.FastExtension) and \
               self.peer.torrent.data_manager.bitfield.has_none:
                    Logger().write(1, "Got nothing, sending HaveNone")
                    self.peer.connection_manager.send(HaveNoneMessage().to_bytes())
            else:
                Logger().write(1, "Sending bitfield message")
                self.peer.connection_manager.send(BitfieldMessage(self.peer.torrent.data_manager.bitfield.get_bitfield()).to_bytes())

        if self.peer.communication_state.out_interest == PeerInterestedState.Uninterested and self.peer.download_manager.has_interesting_pieces():
            Logger().write(1, str(self.peer.id) + ' Sending interested message')
            self.peer.communication_state.out_interest = PeerInterestedState.Interested
            self.peer.connection_manager.send(InterestedMessage().to_bytes())

        if self.peer.extension_manager.peer_supports(ExtensionName.PeerExchange):
            pass

        if self.peer.counter.value < self.peer.low_max_download_speed:
            self.peer.peer_speed = PeerSpeed.Low
        elif self.peer.counter.value < self.peer.medium_max_download_speed:
            self.peer.peer_speed = PeerSpeed.Medium
        else:
            self.peer.peer_speed = PeerSpeed.High

        return True

    def handshake(self):
        message = HandshakeMessage(self.peer.torrent.info_hash.sha1_hashed_bytes)
        message.reserved = ProtocolExtensionManager.add_extensions_to_handshake(message.reserved)

        Logger().write(1, "Sending handshake")
        self.peer.connection_manager.send(message.to_bytes())

        answer = None
        start_time = current_time()
        while not answer:
            if self.peer.connection_manager.connection_state == ConnectionState.Disconnected:
                break

            answer = self.peer.connection_manager.get_message()
            if current_time() - start_time > 5000:
                break
            if not answer:
                sleep(0.2)

        if answer is None or len(answer) == 0:
            Logger().write(1, str(self.peer.id) + ' did not receive handshake response')
            return False

        response = HandshakeMessage.from_bytes(answer)
        if response is None:
            Logger().write(1, str(self.peer.id) + ' invalid handshake response')
            return False

        if response.protocol != b'BitTorrent protocol':
            Logger().write(2, 'Unknown bittorrent protocol, disconnecting. ' + str(response.protocol))
            return False

        self.peer.extension_manager.parse_extension_bytes(response.reserved)
        Logger().write(1, "Received valid handshake response")
        self.handshake_successful = True
        return True

    def stop(self):
        self.peer = None