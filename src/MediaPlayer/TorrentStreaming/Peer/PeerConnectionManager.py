from threading import Lock

from MediaPlayer.TorrentStreaming.Peer.PeerMessages import KeepAliveMessage
from MediaPlayer.Util.Enums import ConnectionState, ReceiveState
from MediaPlayer.Util.Network import *
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import TcpClient
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time


class PeerConnectionManager:

    def __init__(self, peer, uri, on_connect, on_disconnect):
        self.peer = peer
        self.uri = uri
        self.received_bytes = []
        self.to_send_bytes = bytearray()
        self.connection_state = ConnectionState.Initial
        self.connected_on = 0
        self.last_communication = 0
        self.sendLock = Lock()
        self.receiveLock = Lock()
        self.peer_timeout = Settings.get_int("peer_timeout")
        self.connection_timeout = Settings.get_int("connection_timeout") / 1000
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self.connection = TcpClient(uri.hostname, uri.port, self.connection_timeout)
        self.buffer = bytearray()
        self.next_message_length = 68
        self.buffer_position = 0
        self.receive_state = ReceiveState.ReceiveMessage

    def start(self):
        self.connection_state = ConnectionState.Connecting
        self.connected_on = 0
        Logger().write(LogVerbosity.All, str(self.peer.id) + ' connecting to ' + str(self.uri.netloc))
        Stats.add('peers_connect_try', 1)

        if not self.connection.connect():
            Stats.add('peers_connect_failed', 1)
            Logger().write(LogVerbosity.All, str(self.peer.id) + ' could not connect to ' + str(self.uri.netloc))
            self.disconnect()
            return

        self.connected_on = current_time()
        self.on_connect()
        Stats.add('peers_connect_success', 1)
        Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' connected to ' + str(self.uri.netloc))
        self.connection_state = ConnectionState.Connected
        self.connection.socket.setblocking(0)

    def handle_read(self):
        if self.connection_state != ConnectionState.Connected:
            return 0

        data = self.connection.receive_available(self.next_message_length)
        if data is None or len(data) == 0:
            self.disconnect()
            return 0

        self.buffer[self.buffer_position:] = data
        self.last_communication = current_time()

        data_length = len(data)
        if data_length < self.next_message_length:
            # incomplete message
            self.next_message_length -= data_length
            self.buffer_position += data_length
            return data_length
        else:
            if self.receive_state == ReceiveState.ReceiveLength:
                offset, msg_length = read_integer(self.buffer, 0)
                self.next_message_length = msg_length
                self.buffer_position = 0
                self.receive_state = ReceiveState.ReceiveMessage
                self.buffer.clear()

                if self.next_message_length < 0 or self.next_message_length > 17000:
                    Logger().write(LogVerbosity.Info, "Invalid next message length: " + str(self.next_message_length))
                    self.disconnect()

                return data_length
            else:
                total_data = data_length + self.buffer_position
                message = bytes(self.buffer[0: total_data])
                self.buffer.clear()
                self.next_message_length = 4
                self.buffer_position = 0
                self.receive_state = ReceiveState.ReceiveLength

                with self.receiveLock:
                    self.received_bytes.append(message)

                return data_length

    def handle_write(self):
        if self.connection_state != ConnectionState.Connected:
            return

        success = True
        with self.sendLock:
            if len(self.to_send_bytes) != 0:
                success = self.connection.send(self.to_send_bytes)
                self.to_send_bytes.clear()
                self.last_communication = current_time()

        if not success:
            self.disconnect()

    def send(self, data):
        with self.sendLock:
            self.to_send_bytes.extend(data)

    def get_message(self):
        if len(self.received_bytes) == 0:
            return None

        with self.receiveLock:
            data = self.received_bytes.pop(0)

        return data

    def update(self):
        if self.connection_state == ConnectionState.Initial:
            self.start()
        if self.connection_state == ConnectionState.Connected \
                and self.last_communication < current_time() - self.peer_timeout \
                and self.connected_on < current_time() - 30000:
            Logger().write(LogVerbosity.Debug, "Sending keep alive")
            self.send(KeepAliveMessage().to_bytes())
        if self.connection_state == ConnectionState.Disconnected:
            return False
        return True

    def log(self):
        Logger().write(LogVerbosity.Important, "       Last communication: " + str(current_time() - self.last_communication) + "ms ago")
        Logger().write(LogVerbosity.Important, "       To send buffer length: " + str(len(self.to_send_bytes)))
        Logger().write(LogVerbosity.Important, "       Receive buffer length: " + str(len(self.received_bytes)))

    def disconnect(self):
        if self.connection_state == ConnectionState.Disconnected:
            return

        Logger().write(LogVerbosity.Debug, str(self.peer.id) + ' disconnected')
        self.connection_state = ConnectionState.Disconnected

        with self.sendLock:
            self.to_send_bytes.clear()

        with self.receiveLock:
            self.received_bytes.clear()

        self.connection.disconnect()
        self.on_disconnect()
