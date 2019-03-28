from MediaPlayer.Util.Enums import ConnectionState, ReceiveState, PeerState
from MediaPlayer.Util.Network import *
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import TcpClient
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time


class PeerConnectionManager(LogObject):

    @property
    def ready_for_sending(self):
        return len(self.to_send_bytes) > 0 and current_time() - self.last_send > 50

    def __init__(self, peer, uri):
        super().__init__(peer, "Connection manager")

        self.peer = peer
        self.uri = uri
        self.to_send_bytes = bytearray()
        self.last_send = 0
        self.connection_state = ConnectionState.Initial
        self.connected_on = 0
        self._last_communication = 0
        self._peer_timeout = Settings.get_int("peer_timeout")
        self._connection_timeout = Settings.get_int("connection_timeout") / 1000

        self.connection = TcpClient(uri.hostname, uri.port, self._connection_timeout)
        self.buffer = bytearray()
        self._next_message_length = 0
        self._buffer_position = 0
        self._receive_state = ReceiveState.ReceiveLength
        self.receive_buffer_size = 32768

        self.reading_handshake = True

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
        self.peer.add_connected_peer_stat(self.peer.source)
        Stats.add('peers_connect_success', 1)
        Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' connected to ' + str(self.uri.netloc))
        self.connection_state = ConnectionState.Connected
        self.peer.state = PeerState.Started

    def handle_read(self):
        if self.connection_state != ConnectionState.Connected:
            return 0, []

        data = self.connection.receive_available(self.receive_buffer_size)
        if data is None or len(data) == 0:
            self.peer.stop_async()
            return 0, []

        received_messages = []
        messages_size = 0

        self.buffer += data
        self._last_communication = current_time()
        buffer_size = len(self.buffer)

        while True:
            if buffer_size - self._buffer_position < self._next_message_length:
                # cant read another complete message
                break

            # form messages from the buffer:
            if self._receive_state == ReceiveState.ReceiveLength:
                if self.reading_handshake:
                    offset, id_length = read_byte_as_int(self.buffer, 0)
                    msg_length = id_length + 49  # Handshake sends the length of the id, the rest of the handshake takes 49 bytes
                    if msg_length > len(self.buffer):
                        break
                    self.reading_handshake = False
                else:
                    offset, msg_length = read_integer(self.buffer, self._buffer_position)
                    self._buffer_position += 4

                self._next_message_length = msg_length
                self._receive_state = ReceiveState.ReceiveMessage

                if self._next_message_length < 0 or self._next_message_length > 17000:
                    Logger().write(LogVerbosity.Info, "Invalid next message length: " + str(self._next_message_length))
                    self.peer.stop_async()
                    break
            else:
                total_data = self._buffer_position + self._next_message_length
                message = bytes(self.buffer[self._buffer_position: total_data])
                self._buffer_position = total_data
                self._next_message_length = 4
                self._receive_state = ReceiveState.ReceiveLength
                messages_size += len(message)
                received_messages.append(message)

        self.buffer = self.buffer[self._buffer_position:]
        self._buffer_position = 0
        return messages_size, received_messages

    def handle_write(self):
        if self.connection_state != ConnectionState.Connected:
            return

        success = True
        if len(self.to_send_bytes) != 0:
            success = self.connection.send(self.to_send_bytes)
            self.to_send_bytes.clear()
            self.to_send_bytes_log = 0
            self.last_send = current_time()
            self._last_communication = current_time()

        if not success:
            self.peer.stop_async()

    def send(self, data):
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

        self.to_send_bytes.clear()
        self.to_send_bytes_log = 0

        self.connection.disconnect()
        self.buffer.clear()
