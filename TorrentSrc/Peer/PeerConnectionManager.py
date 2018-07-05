import time
from threading import Lock

from Shared.Logger import *
from Shared.Stats import Stats
from Shared.Util import current_time
from TorrentSrc.Connections import TcpClient
from TorrentSrc.Peer.PeerMessages import KeepAliveMessage
from TorrentSrc.Util.Enums import ConnectionState, ReceiveState
from TorrentSrc.Util.Network import *


class PeerConnectionManager:

    def __init__(self, peer, uri):
        self.peer = peer
        self.uri = uri
        self.received_bytes = []
        self.to_send_bytes = bytearray()
        self.on_disconnect = None
        self.connection_state = ConnectionState.Initial
        self.connected_on = 0
        self.last_communication = 0
        self.sendLock = Lock()
        self.receiveLock = Lock()
        self.peer_timeout = Settings.get_int("peer_timeout")
        self.connection_timeout = Settings.get_int("connection_timeout") / 1000

        self.connection = TcpClient(uri.hostname, uri.port)
        self.buffer = bytearray()
        self.next_message_length = 68
        self.buffer_position = 0
        self.receive_state = ReceiveState.ReceiveMessage

    def start(self):
        self.connection_state = ConnectionState.Connecting
        Logger.write(1, str(self.peer.id) + ' connecting to ' + str(self.uri.netloc))
        Stats['peers_connect_try'].add(1)

        if not self.connection.connect(self.connection_timeout):
            Stats['peers_connect_failed'].add(1)
            Logger.write(1, str(self.peer.id) + ' could not connect to ' + str(self.uri.netloc))
            self.disconnect()
            return

        self.connected_on = current_time()
        Stats['peers_connect_success'].add(1)
        Logger.write(1, str(self.peer.id) + ' connected to ' + str(self.uri.netloc))
        self.connection_state = ConnectionState.Connected
        self.connection.socket.setblocking(0)

    def on_readable(self):
        self.handle_read()

    def on_writeable(self):
        self.handle_write()

    def handle_read(self):
        if self.connection_state != ConnectionState.Connected:
            return

        data = self.connection.receive_available(self.next_message_length)
        if data is None or len(data) == 0:
            self.disconnect()
            return

        self.buffer[self.buffer_position:] = data

        data_length = len(data)
        if data_length < self.next_message_length:
            # incomplete message
            self.next_message_length -= data_length
            self.buffer_position += data_length
            return
        else:
            if self.receive_state == ReceiveState.ReceiveLength:
                offset, msg_length = read_integer(self.buffer, 0)
                self.next_message_length = msg_length
                self.buffer_position = 0
                self.receive_state = ReceiveState.ReceiveMessage
                self.buffer.clear()

                if self.next_message_length < 0 or self.next_message_length > 17000:
                    Logger.write(2, "Invalid next message length: " + str(self.next_message_length))
                    self.disconnect()
                else:
                    Logger.write(1, "Next message length: " + str(self.next_message_length))

                return
            else:
                total_data = data_length + self.buffer_position
                message = bytes(self.buffer[0: total_data])
                self.buffer.clear()
                self.next_message_length = 4
                self.buffer_position = 0
                self.receive_state = ReceiveState.ReceiveLength

                self.receiveLock.acquire()
                self.received_bytes.append(message)
                self.receiveLock.release()

                return

    def handle_write(self):
        if self.connection_state != ConnectionState.Connected:
            return

        success = True
        self.sendLock.acquire()
        if len(self.to_send_bytes) != 0:
            Logger.write(1, str(self.peer.id) + ' Sending ' + str(len(self.to_send_bytes)) + " bytes of data")
            success = self.connection.send(self.to_send_bytes)
            self.to_send_bytes.clear()
            self.last_communication = current_time()
        self.sendLock.release()

        if not success:
            self.disconnect()

    def send(self, data):
        self.sendLock.acquire()
        self.to_send_bytes.extend(data)
        self.sendLock.release()

    def get_message(self):
        if len(self.received_bytes) == 0:
            return None

        self.receiveLock.acquire()
        data = self.received_bytes.pop(0)
        self.receiveLock.release()

        return data

    def update(self):
        if self.connection_state == ConnectionState.Initial:
            self.start()
        if self.connection_state == ConnectionState.Connected and self.last_communication < current_time() - self.peer_timeout and self.connected_on < current_time() - 30000:
            Logger.write(1, "Sending keep alive")
            self.send(KeepAliveMessage().to_bytes())
        if self.connection_state == ConnectionState.Disconnected:
            return False
        return True

    def log(self):
        Logger.write(3, "       Last communication: " + str(current_time() - self.last_communication) +"ms ago")
        Logger.write(3, "       To send buffer length: " + str(len(self.to_send_bytes)))
        Logger.write(3, "       Receive buffer length: " + str(len(self.received_bytes)))

    def disconnect(self):
        if self.connection_state == ConnectionState.Disconnected:
            return

        Logger.write(1, str(self.peer.id) + ' disconnected')
        self.connection_state = ConnectionState.Disconnected

        self.sendLock.acquire()
        self.to_send_bytes.clear()
        self.sendLock.release()

        self.receiveLock.acquire()
        self.received_bytes.clear()
        self.receiveLock.release()

        self.connection.disconnect()

        self.peer.stop()
