import random
import threading
import time

from Shared.Logger import Logger
from Utp.UtpConnection import UtpConnection
from Utp.UtpObjects import UtpPacket, ConnectionState, MessageType


class UtpClient:

    def __init__(self, host=None, port=None):
        if host is not None:
            self.host = host
        if port is not 0:
            self.port = port
        else:
            self.port = 0

        self.receive_packet_size = 65535
        self.send_packet_size = 1400
        self.max_window_size = 1048576

        self.connection_state = ConnectionState.CS_INITIAL

        self.connection_id = random.randint(0, 65535)
        self.receive_connection_id = self.connection_id + 1

        self.seq_nr = random.randint(0, 65535)
        self.ack_nr = 0
        self.timestamp_dif = 0

        self.running = False
        self.utp_connection = UtpConnection(self.host, self.port)
        self.socket = self.utp_connection.socket
        self.unacked = []

        self.receive_pkt_buffer = [] # holds packages until the can be re-assembled in order
        self.receive_buffer = bytes() # received data buffer
        self.send_buffer = bytes() # send data buffer

        self.connect_event = threading.Event()
        self.receive_event = threading.Event()

    def connect(self, timeout=5):
        if self.port == 0:
            self.port = 6881
        self.running = True
        self.connection_state = ConnectionState.CS_SYN_SENT

        self.send_packet(UtpPacket(MessageType.ST_SYN, 1, 0, self.connection_id, 0, 0, 0, 0, 0))
        return self.connect_event.wait(timeout)

    def send(self, data):
        self.send_buffer += data
        return True

    def receive_available(self, max_amount):
        if len(self.receive_buffer) == 0:
            self.receive_event.wait()
            self.receive_event.clear()
            return self.receive_available(max_amount)
        if len(self.receive_buffer) < max_amount:
            data = self.receive_buffer
            self.receive_buffer = bytes()
            return data

        data = self.receive_buffer[0: max_amount]
        self.receive_buffer = self.receive_buffer[max_amount:]
        return data

    def disconnect(self):
        if self.connection_state == ConnectionState.CS_CONNECTED:
            self.send_packet(UtpPacket(MessageType.ST_RESET, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))
        self.connection_state = ConnectionState.CS_DISCONNECTED

    def process_send(self):
        if len(self.send_buffer) != 0:
            while len(self.send_buffer) != 0:
                if len(self.send_buffer) > self.send_packet_size:
                    to_send = self.send_buffer[0:self.send_packet_size]
                    self.send_buffer = self.send_buffer[self.send_packet_size:]
                else:
                    to_send = self.send_buffer
                    self.send_buffer = bytes()

                self.send_packet(UtpPacket(MessageType.ST_DATA, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0, to_send))
        self.utp_connection.flush()

    def send_packet(self, packet):
        if packet.data is not None or packet.message_type == MessageType.ST_SYN:
            self.seq_nr += 1
            self.unacked.append(packet)

        packet.timestamp = self.time()
        packet.ack_nr = self.ack_nr
        packet.seq_nr = self.seq_nr
        packet.wnd_size = self.max_window_size - len(self.receive_buffer)
        packet.timestamp_dif = self.timestamp_dif

        Logger.write(1, "Sending utp packet: " + str(packet))
        self.utp_connection.send(packet)

    def handle_packet(self, data):
        pkt = UtpPacket.from_bytes(data)
        Logger.write(1, "Received utp packet: " + str(pkt))
        if self.connection_state != ConnectionState.CS_INITIAL and pkt.connection_id != self.connection_id:
            Logger.write(1, "Unexpected connection_id: " + str(pkt.connection_id) + ", expected: " + str(self.connection_id))

        self.process_packet(pkt)
        while True:
            pkts = [pkt for pkt in self.receive_pkt_buffer if pkt.seq_nr == self.ack_nr + 1]
            if len(pkts) == 0:
                break
            Logger.write(1, "Picking up earlier received packet")
            self.process_packet(pkt[0])

    def process_packet(self, pkt):
        Logger.write(1, "Processing utp packet: " + str(pkt))
        self.ack_nr = pkt.seq_nr
        self.timestamp_dif = abs(self.time() - pkt.timestamp)

        if pkt.message_type == MessageType.ST_STATE:
            acked_pkt = [p for p in self.unacked if pkt.ack_nr == p.seq_nr]
            if len(acked_pkt) == 0:
                Logger.write(1, "Received ack for packet we didn't send? AckNr: " + str(pkt.ack_nr))
            else:
                self.unacked.remove(acked_pkt[0])

            if self.connection_state == ConnectionState.CS_SYN_SENT:
                Logger.write(1, "Received ST_State after sending ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED
                self.ack_nr -= 1
                self.connect_event.set()

        elif pkt.message_type == MessageType.ST_DATA:
            if self.connection_state == ConnectionState.CS_SYN_RECV:
                Logger.write(1, "Received ST_Data after receiving ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED

            self.send_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

            self.receive_buffer += pkt.data
            self.receive_event.set()

        elif pkt.message_type == MessageType.ST_SYN:
            self.connection_id = pkt.connection_id
            self.receive_connection_id = self.connection_id + 1
            self.seq_nr = random.randint(0, 65535)
            self.connection_state = ConnectionState.CS_SYN_RECV
            Logger.write(1, "Received ST_Syn; CS_SYN_RECV")
            self.send_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

    def time(self):
        cur_time = int(str(time.time())[-11:].replace('.', ''))
        while cur_time > 0xFFFFFFFF:
            cur_time -= 0xFFFFFFFF
        return cur_time

