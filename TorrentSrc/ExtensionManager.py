from TorrentSrc.Util import Bencode
from TorrentSrc.Util.Enums import ExtensionName, ExtensionType, ExtensionProtocolMessageType


class ProtocolExtension:

    def __init__(self, extension_name, id_name, extension_type, reserved_id, bit_mask, supported):
        self.extension_name = extension_name
        self.id_name = id_name
        self.extension_type = extension_type
        self.reserved_id = reserved_id
        self.bit_mask = bit_mask
        self.supported = supported


class ProtocolExtensionManager:

    known_extensions = [
        ProtocolExtension(ExtensionName.FastExtension, "", ExtensionType.Basic, 7, 0x04, True),
        ProtocolExtension(ExtensionName.ExtensionProtocol, "", ExtensionType.Basic, 5, 0x10, True),
        ProtocolExtension(ExtensionName.DHT, "", ExtensionType.Basic, 7, 0x01, True),
        ProtocolExtension(ExtensionName.PeerExchange, "ut_pex", ExtensionType.Extension, ExtensionProtocolMessageType.PeerExchange, 0, True),
        ProtocolExtension(ExtensionName.Metadata, "ut_metadata", ExtensionType.Extension, ExtensionProtocolMessageType.Metadata, 0, True)
    ]

    @staticmethod
    def get_extension(name):
        filtered = [x for x in ProtocolExtensionManager.known_extensions if x.extension_name == name]
        if len(filtered) == 1:
            return filtered[0]

    @staticmethod
    def get_extension_by_id_name(name):
        filtered = [x for x in ProtocolExtensionManager.known_extensions if x.id_name == name]
        if len(filtered) == 1:
            return filtered[0]

    @staticmethod
    def get_extensions():
        return ProtocolExtensionManager.known_extensions.copy()

    @staticmethod
    def add_extensions_to_handshake(byte):
        for ext in [x for x in ProtocolExtensionManager.known_extensions if x.extension_type == ExtensionType.Basic and x.supported]:
            byte[ext.reserved_id] |= ext.bit_mask
        return byte

    @staticmethod
    def create_extension_dictionary():
        dic = dict()
        m_dic = dict()
        for ext in [x for x in ProtocolExtensionManager.known_extensions if x.extension_type == ExtensionType.Extension and x.supported]:
            m_dic[ext.id_name.encode('utf8')] = int(ext.reserved_id)
        dic[b'm'] = m_dic
        return Bencode.bencode(dic)
