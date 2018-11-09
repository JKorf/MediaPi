import abc

from Shared.Logger import Logger
from MediaPlayer.Util import Bencode
from MediaPlayer.Util import Network
from MediaPlayer.Util.Enums import PeerMessageType, ExtensionProtocolMessageType, MetadataMessageType, ExtensionName
from MediaPlayer.Util.Util import uri_to_bytes, uri_from_bytes, check_bytes_length, check_minimal_bytes_length


class HandshakeMessage:

    def __init__(self, info_hash_bytes):
        self.length = 19
        self.protocol = b"BitTorrent protocol"
        self.reserved = bytearray(8)
        self.info_hash = info_hash_bytes
        self.peer_id = b'-JK0001-100000100000'

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 68):
            return None

        offset = 0
        offset, length = Network.read_byte_as_int(data, offset)
        offset, protocol = Network.read_bytes(data, 19, offset)
        offset, reserved = Network.read_bytes(data, 8, offset)
        offset, info_hash = Network.read_bytes(data, 20, offset)
        offset, peer_id = Network.read_bytes(data, 20, offset)

        result = cls(info_hash)
        result.length = length
        result.protocol = protocol
        result.reserved = reserved
        result.peer_id = peer_id

        return result

    def to_bytes(self):
        result = bytearray(68)
        offset = 0
        offset = Network.write_int_as_byte(result, self.length, offset)
        result[1: 20] = self.protocol
        offset += 19
        offset = Network.write_bytes(result, self.reserved, offset)
        Network.write_bytes(result, self.info_hash, offset)
        result[48: 68] = self.peer_id

        return result


class BasePeerMessage:

    @property
    def total_length(self):
        return self.length + 4

    def __init__(self, type):
        self.length = 0
        self.message_type = type

    @abc.abstractmethod
    def to_bytes(self):
        return

    @staticmethod
    def from_bytes(peer, data):
        length = len(data)
        if length == 0:
            return KeepAliveMessage()

        offset, type = Network.read_byte_as_int(data, 0)
        if type == PeerMessageType.Piece: return PieceMessage.from_bytes(data)
        if type == PeerMessageType.Choke: return ChokeMessage.from_bytes(data)
        if type == PeerMessageType.Unchoke: return UnchokeMessage.from_bytes(data)
        if type == PeerMessageType.Interested: return InterestedMessage.from_bytes(data)
        if type == PeerMessageType.Uninterested: return UninterestedMessage.from_bytes(data)
        if type == PeerMessageType.Have: return HaveMessage.from_bytes(data)
        if type == PeerMessageType.Bitfield: return BitfieldMessage.from_bytes(data)
        if type == PeerMessageType.Request: return RequestMessage.from_bytes(data)
        if type == PeerMessageType.Port: return PortMessage.from_bytes(data)
        if type == PeerMessageType.Cancel: return CancelMessage.from_bytes(data)
        if type == PeerMessageType.HaveAll: return HaveAllMessage.from_bytes(data)
        if type == PeerMessageType.HaveNone: return HaveNoneMessage.from_bytes(data)
        if type == PeerMessageType.AllowedFast: return AllowedFastMessage.from_bytes(data)
        if type == PeerMessageType.SuggestPiece: return SuggestPieceMessage.from_bytes(data)
        if type == PeerMessageType.RejectRequest: return RejectRequestMessage.from_bytes(data)

        if type == PeerMessageType.ExtensionMessage:
            offset, extension_message_type = Network.read_byte_as_int(data, offset)
            if extension_message_type == 0: return ExtensionHandshakeMessage.from_bytes(data)
            if extension_message_type == ExtensionProtocolMessageType.PeerExchange: return PeerExchangeMessage.from_bytes(data)
            if extension_message_type == ExtensionProtocolMessageType.Metadata: return MetadataMessage.from_bytes(data)

        Logger.write(2, "Unknown message! type = " + str(type))


class KeepAliveMessage:

    def __init__(self):
        self.total_length = 4

    def to_bytes(self):
        result = bytearray(4)
        Network.write_int(result, 0, 0)
        return result


class ChokeMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.Choke)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None
        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class UnchokeMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.Unchoke)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None
        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class InterestedMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.Interested)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None
        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class UninterestedMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.Uninterested)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None
        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class HaveMessage(BasePeerMessage):

    def __init__(self, piece_index):
        BasePeerMessage.__init__(self, PeerMessageType.Have)
        self.length = 5
        self.piece_index = piece_index

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 5):
            return None

        offset, piece_index = Network.read_integer(data, 1)
        return cls(piece_index)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        Network.write_int(result, self.piece_index, offset)
        return result


class BitfieldMessage(BasePeerMessage):
    def __init__(self, bitfield):
        BasePeerMessage.__init__(self, PeerMessageType.Bitfield)
        self.length = 1 + len(bitfield)
        self.bitfield = bitfield

    @classmethod
    def from_bytes(cls, data):
        if not check_minimal_bytes_length(data, 2):
            return None

        offset, bitfield = Network.read_bytes(data, len(data) - 1, 1)
        return cls(bitfield)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        Network.write_bytes(result, self.bitfield, offset)
        return result


class RequestMessage(BasePeerMessage):

    def __init__(self, index, offset, length):
        BasePeerMessage.__init__(self, PeerMessageType.Request)
        self.length = 13
        self.index = index
        self.offset = offset
        self.data_length = length

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 13):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)
        offset, data_offset = Network.read_integer(data, offset)
        offset, data_length = Network.read_integer(data, offset)
        return cls(piece_index, data_offset, data_length)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int(result, self.index, offset)
        offset = Network.write_int(result, self.offset, offset)
        Network.write_int(result, self.data_length, offset)
        return result


class PieceMessage(BasePeerMessage):

    def __init__(self, index, offset, data):
        BasePeerMessage.__init__(self, PeerMessageType.Piece)
        self.length = 9 + len(data)
        self.index = index
        self.offset = offset
        self.data = data

    @classmethod
    def from_bytes(cls, data):
        if not check_minimal_bytes_length(data, 10):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)
        offset, data_offset = Network.read_integer(data, offset)
        offset, data_bytes = Network.read_bytes(data, len(data) - offset, offset)
        return cls(piece_index, data_offset, data_bytes)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int(result, self.index, offset)
        offset = Network.write_int(result, self.offset, offset)
        Network.write_bytes(result, self.data, offset)
        return result


class PortMessage(BasePeerMessage):

    def __init__(self, port):
        BasePeerMessage.__init__(self, PeerMessageType.Port)
        self.length = 3
        self.port = port

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 3):
            return None

        offset, port = Network.read_ushort(data, 1)
        return cls(port)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        Network.write_ushort(result, self.port, offset)
        return result


class CancelMessage(BasePeerMessage):

    def __init__(self, index, offset, length):
        BasePeerMessage.__init__(self, PeerMessageType.Cancel)
        self.length = 13
        self.index = index
        self.offset = offset
        self.data_length = length

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 13):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)
        offset, data_offset = Network.read_integer(data, offset)
        offset, data_length = Network.read_integer(data, offset)
        return cls(piece_index, data_offset, data_length)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int(result, self.index, offset)
        offset = Network.write_int(result, self.offset, offset)
        Network.write_int(result, self.data_length, offset)
        return result


# extension messages

class ExtensionHandshakeMessage(BasePeerMessage):

    def __init__(self, payload):
        BasePeerMessage.__init__(self, PeerMessageType.ExtensionMessage)

        self.type = ExtensionProtocolMessageType.Handshake
        self.bencoded_payload = payload
        self.length = 2 + len(payload)

    @classmethod
    def from_bytes(cls, data):
        if not check_minimal_bytes_length(data, 3):
            return None

        offset, payload = Network.read_bytes(data, len(data) - 2, 2)
        return cls(payload)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int_as_byte(result, self.type, offset)
        Network.write_bytes(result, self.bencoded_payload, offset)

        return result


class PeerExchangeMessage(BasePeerMessage):

    def __init__(self, added, dropped):
        BasePeerMessage.__init__(self, PeerMessageType.ExtensionMessage)

        self.type = ExtensionProtocolMessageType.PeerExchange
        self.dropped = dropped
        self.added = added

    @classmethod
    def from_bytes(cls, data):
        added = []
        dropped = []

        offset, payload_data = Network.read_bytes(data, len(data) - 2, 2)
        payload = Bencode.bdecode(payload_data)
        if b'added' in payload:
            addedbytes = payload[b'added']
            total_peers = int(len(addedbytes) / 6)
            offset = 0
            for index in range(total_peers):
                added.append(uri_from_bytes(addedbytes[offset:offset + 6]))
                offset += 6

        return cls(added, dropped)

    def to_bytes(self):
        result = dict()
        added_result = bytearray()
        flag_result = bytearray()
        index = 0

        for uri in self.added:
            added_result[index: index + 6] = uri_to_bytes(uri)
            flag_result.append(0x10)
            index += 6

        result[b'added'] = bytes(added_result)
        result[b'added.f'] = bytes(flag_result)
        bencoded = Bencode.bencode(result)

        self.length = len(bencoded) + 2
        result_bytes = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result_bytes, self.length, offset)
        offset = Network.write_int_as_byte(result_bytes, self.message_type, offset)
        offset = Network.write_int_as_byte(result_bytes, self.type, offset)
        Network.write_bytes(result_bytes, bencoded, offset)
        return result_bytes


class MetadataMessage(BasePeerMessage):

    def __init__(self, peer, type, piece_index, total_size=0, data=None):
        BasePeerMessage.__init__(self, PeerMessageType.ExtensionMessage)
        if peer is None:
            self.type = ExtensionProtocolMessageType.Metadata
        else:
            self.type = peer.extension_manager.get_id_for_message(ExtensionName.Metadata)

        self.metadata_message_type = type
        self.piece_index = piece_index
        self.total_metadata_size = total_size
        self.data = data

    @classmethod
    def from_bytes(cls, data):
        if not check_minimal_bytes_length(data, 2):
            return None

        offset, payload_data = Network.read_bytes(data, len(data) - 2, 2)
        payload = Bencode.bdecode(payload_data)

        metadata_message_type = payload[b'msg_type']
        piece_index = payload[b'piece']
        total_size = 0
        metadata = None
        if metadata_message_type == MetadataMessageType.Data:
            if b'total_size' not in payload:
                return None
            total_size = payload[b'total_size']
            metadata = data[2 + len(Bencode.bencode(payload)): len(data)]

        return cls(None, metadata_message_type, piece_index, total_size, metadata)

    def to_bytes(self):
        result = dict()
        result[b'msg_type'] = self.metadata_message_type
        result[b'piece'] = self.piece_index
        data = Bencode.bencode(result)
        self.length = 2 + len(data)
        result = bytearray(self.total_length)
        offset = 0

        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int_as_byte(result, self.type, offset)
        Network.write_bytes(result, data, offset)
        return result


class HaveAllMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.HaveAll)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None

        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class HaveNoneMessage(BasePeerMessage):

    def __init__(self):
        BasePeerMessage.__init__(self, PeerMessageType.HaveNone)
        self.length = 1

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 1):
            return None

        return cls()

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        Network.write_int_as_byte(result, self.message_type, offset)
        return result


class AllowedFastMessage(BasePeerMessage):

    def __init__(self, piece_index):
        BasePeerMessage.__init__(self, PeerMessageType.AllowedFast)
        self.length = 5
        self.piece_index = piece_index

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 5):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)

        return cls(piece_index)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        Network.write_int(result, self.piece_index, offset)
        return result


class SuggestPieceMessage(BasePeerMessage):

    def __init__(self, piece_index):
        BasePeerMessage.__init__(self, PeerMessageType.SuggestPiece)
        self.length = 5
        self.piece_index = piece_index

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 5):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)

        return cls(piece_index)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        Network.write_int(result, self.piece_index, offset)
        return result


class RejectRequestMessage(BasePeerMessage):

    def __init__(self, index, offset, length):
        BasePeerMessage.__init__(self, PeerMessageType.RejectRequest)
        self.length = 13
        self.index = index
        self.offset = offset
        self.data_length = length

    @classmethod
    def from_bytes(cls, data):
        if not check_bytes_length(data, 13):
            return None

        offset = 1
        offset, piece_index = Network.read_integer(data, offset)
        offset, data_offset = Network.read_integer(data, offset)
        offset, data_length = Network.read_integer(data, offset)
        return cls(piece_index, data_offset, data_length)

    def to_bytes(self):
        result = bytearray(self.total_length)
        offset = 0
        offset = Network.write_int(result, self.length, offset)
        offset = Network.write_int_as_byte(result, self.message_type, offset)
        offset = Network.write_int(result, self.index, offset)
        offset = Network.write_int(result, self.offset, offset)
        Network.write_int(result, self.data_length, offset)
        return result
