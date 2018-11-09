from MediaPlayer.TorrentStreaming.ExtensionManager import ProtocolExtensionManager
from MediaPlayer.Util.Enums import ExtensionType
from Shared.Logger import Logger


class PeerExtensionManager:

    def __init__(self, peer):
        self.peer = peer
        self.supported_peer_extensions = dict()
        self.extension_bytes = None
        self.extension_dict = None
        self.original_data = None

    def parse_extension_bytes(self, data):
        self.original_data = data
        known_extensions = ProtocolExtensionManager.get_extensions()
        for extension in [x for x in known_extensions if x.extension_type == ExtensionType.Basic]:
            if data[extension.reserved_id] & extension.bit_mask != 0:
                self.supported_peer_extensions[extension.extension_name] = 0

    def parse_dictionary(self, data):
        dic = data[b'm']
        self.extension_dict = dic
        for key, value in dic.items():
            extension = ProtocolExtensionManager.get_extension_by_id_name(key.decode('utf8'))
            if extension is not None:
                Logger.write(1, str(self.peer.id) + ' Peer supports ' + key.decode('utf8'))
                self.supported_peer_extensions[extension.extension_name] = value
            else:
                Logger.write(1, str(self.peer.id) + ' Unknown peer extension: ' + key.decode('utf8'))

    def peer_supports(self, name):
        return name in self.supported_peer_extensions

    def get_id_for_message(self, name):
        if name in self.supported_peer_extensions:
            return self.supported_peer_extensions[name]
        return None
