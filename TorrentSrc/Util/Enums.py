class TorrentState:
    Initial = 1
    DownloadingMetaData = 2
    Downloading = 3
    Paused = 4
    Done = 5


class OutputMode:
    Stream = 1
    File = 2


class PeerMessageType:
    Choke = 0
    Unchoke = 1
    Interested = 2
    Uninterested = 3
    Have = 4
    Bitfield = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9
    SuggestPiece = 13
    HaveAll = 14
    HaveNone = 15
    RejectRequest = 16
    AllowedFast = 17
    ExtensionMessage = 20


class PeerChokeState:
    Choked = 1
    Unchoked = 2


class PeerInterestedState:
    Interested = 1
    Uninterested = 2


class ConnectionState:
    Initial = 0
    Connecting = 1
    Connected = 2
    Disconnected = 3


class ExtensionType:
    Basic = 1
    Extension = 2


class ExtensionName:
    FastExtension = 1
    ExtensionProtocol = 2
    PeerExchange = 3
    Metadata = 4
    DHT = 5


class ExtensionProtocolMessageType:
    Handshake = 0
    PeerExchange = 1
    Metadata = 2


class PeerSource:
    HttpTracker = 0
    UdpTracker = 1
    PeerExchange = 2
    DHT = 3


class PeerSpeed:
    Low = 1
    Medium = 2
    High = 3


class MetadataMessageType:
    Request = 0
    Data = 1
    Reject = 2


class ReceiveState:
    ReceiveLength = 0
    ReceiveMessage = 1


class DownloadMode:
    Full = 0
    ImportantOnly = 1
