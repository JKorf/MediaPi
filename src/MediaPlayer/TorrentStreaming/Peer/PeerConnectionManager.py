from threading import Lock

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import KeepAliveMessage
from MediaPlayer.Util.Enums import ConnectionState, ReceiveState
from MediaPlayer.Util.Network import *
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import TcpClient
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time


class PeerConnectionManager(LogObject):

    def __init__(self, peer, uri, on_connect):
        super().__init__(peer, "Connection manager")

        self.peer = peer
        self.uri = uri
        self.to_send_bytes = bytearray()
        self.connection_state = ConnectionState.Initial
        self.connected_on = 0
        self._last_communication = 0
        self.sendLock = Lock()
        self.receiveLock = Lock()
        self._peer_timeout = Settings.get_int("peer_timeout")
        self._connection_timeout = Settings.get_int("connection_timeout") / 1000
        self.on_connect = on_connect

        self.connection = TcpClient(uri.hostname, uri.port, self._connection_timeout)
        self.buffer = bytearray()
        self._next_message_length = 68
        self._buffer_position = 0
        self.receive_state = ReceiveState.ReceiveMessage

        # Logging props
        self.to_send_bytes_log = 0

    def start(self):
        self.connection_state = ConnectionState.Connecting
        self.connected_on = 0
        Logger().write(LogVerbosity.All, str(self.peer.id) + ' connecting to ' + str(self.uri.netloc))
        Stats.add('peers_connect_try', 1)

        if not self.connection.connect():
            Stats.add('peers_connect_failed', 1)
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' could not connect to ' + str(self.uri.netloc))
            self.peer.stop_async()
            return

        self.connected_on = current_time()
        self.on_connect()
        Stats.add('peers_connect_success', 1)
        Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' connected to ' + str(self.uri.netloc))
        self.connection_state = ConnectionState.Connected

    def handle_read(self):
        if self.connection_state != ConnectionState.Connected:
            return None

        data = self.connection.receive_available(self._next_message_length)
        if data is None or len(data) == 0:
            self.peer.stop_async()
            return None

        self.buffer[self._buffer_position:] = data
        self._last_communication = current_time()

        data_length = len(data)
        if data_length < self._next_message_length:
            # incomplete message
            self._next_message_length -= data_length
            self._buffer_position += data_length
            return None
        else:
            if self.receive_state == ReceiveState.ReceiveLength:
                offset, msg_length = read_integer(self.buffer, 0)
                self._next_message_length = msg_length
                self._buffer_position = 0
                self.receive_state = ReceiveState.ReceiveMessage
                self.buffer.clear()

                if self._next_message_length < 0 or self._next_message_length > 17000:
                    Logger().write(LogVerbosity.Info, "Invalid next message length: " + str(self._next_message_length))
                    self.peer.stop_async()

                return None
            else:
                total_data = data_length + self._buffer_position
                message = bytes(self.buffer[0: total_data])
                self.buffer.clear()
                self._next_message_length = 4
                self._buffer_position = 0
                self.receive_state = ReceiveState.ReceiveLength
                return message

    def handle_write(self):
        if self.connection_state != ConnectionState.Connected:
            return

        success = True
        with self.sendLock:
            if len(self.to_send_bytes) != 0:
                success = self.connection.send(self.to_send_bytes)
                self.to_send_bytes.clear()
                self.to_send_bytes_log = 0
                self._last_communication = current_time()

        if not success:
            self.peer.stop_async()

    def send(self, data):
        with self.sendLock:
            self.to_send_bytes.extend(data)
            self.to_send_bytes_log = len(data)

    def log(self):
        Logger().write(LogVerbosity.Important, "       Last communication: " + str(current_time() - self._last_communication) + "ms ago")
        Logger().write(LogVerbosity.Important, "       To send buffer length: " + str(len(self.to_send_bytes)))

    def disconnect(self):
        if self.connection_state == ConnectionState.Disconnected:
            return

        Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' disconnected')
        self.connection_state = ConnectionState.Disconnected

        with self.sendLock:
            self.to_send_bytes.clear()
            self.to_send_bytes_log = 0

        self.connection.disconnect()
        self.buffer.clear()
