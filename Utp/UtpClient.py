import random
import threading
import time
from operator import attrgetter

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
        self.other_window_size = 0

        self.last_received_ack = 0
        self.duplicate_acks = 0

        self.running = False
        self.utp_connection = UtpConnection(self.host, self.port)
        self.socket = self.utp_connection.socket
        self.unacked = []

        self.receive_lock = threading.Lock()
        self.receive_pkt_buffer = [] # holds packages until the can be re-assembled in order
        self.receive_buffer = bytes() # received data buffer
        self.send_buffer = bytes() # send data buffer
        self.send_lock = threading.Lock()

        self.connect_event = threading.Event()
        self.receive_event = threading.Event()

    def data_available(self):
        return len(self.receive_buffer) != 0

    def connect(self, timeout=5):
        if self.port == 0:
            self.port = 6881
        self.running = True
        self.connection_state = ConnectionState.CS_SYN_SENT

        self.send_new_packet(UtpPacket(MessageType.ST_SYN, 1, 0, self.connection_id, 0, 0, 0, 0, 0))
        return self.connect_event.wait(timeout)

    def send(self, data):
        self.send_lock.acquire()
        self.send_buffer += data
        self.send_lock.release()
        return True

    def receive_available(self, max_amount):
        if len(self.receive_buffer) == 0:
            self.receive_event.wait()
            self.receive_event.clear()
            return bytes()

        self.receive_lock.acquire()
        if len(self.receive_buffer) < max_amount:
            data = self.receive_buffer
            self.receive_buffer = bytes()
            self.receive_lock.release()
            Logger.write(1, "Removed " + str(len(data)) + " bytes to receive_buffer, now " + str(len(self.receive_buffer)) + " in receive buffer")
            return data

        data = self.receive_buffer[0: max_amount]
        self.receive_buffer = self.receive_buffer[max_amount:]
        Logger.write(1, "Removed " + str(len(data)) + " bytes to receive_buffer, now " + str(
            len(self.receive_buffer)) + " in receive buffer")
        self.receive_lock.release()
        return data

    def disconnect(self):
        self.receive_event.set()
        if self.connection_state == ConnectionState.CS_CONNECTED:
            self.send_new_packet(UtpPacket(MessageType.ST_RESET, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))
        self.connection_state = ConnectionState.CS_DISCONNECTED

    def process_send(self):
        while len(self.send_buffer) != 0:
            self.send_lock.acquire()
            if len(self.send_buffer) > self.send_packet_size:
                to_send = self.send_buffer[0:self.send_packet_size]
                self.send_buffer = self.send_buffer[self.send_packet_size:]
            else:
                to_send = self.send_buffer
                self.send_buffer = bytes()
            self.send_lock.release()
            self.send_new_packet(UtpPacket(MessageType.ST_DATA, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0, to_send))

        self.utp_connection.flush()

    def send_new_packet(self, packet):
        if packet.data is not None or packet.message_type == MessageType.ST_SYN:
            self.seq_nr += 1
            self.unacked.append(packet)
        packet.seq_nr = self.seq_nr
        self.send_packet(packet)

    def send_packet(self, packet):
        packet.timestamp = self.time()
        packet.ack_nr = self.ack_nr
        packet.wnd_size = self.max_window_size - len(self.receive_buffer)
        packet.timestamp_dif = self.timestamp_dif

        self.utp_connection.send(packet)

    def handle_packet(self, data):
        pkt = UtpPacket.from_bytes(data)
        Logger.write(1, "Received utp packet: " + str(pkt))
        if self.connection_state != ConnectionState.CS_INITIAL and pkt.connection_id != self.connection_id:
            Logger.write(1, "Unexpected connection_id: " + str(pkt.connection_id) + ", expected: " + str(self.connection_id))
            return

        if self.ack_nr != 0 and pkt.seq_nr > self.ack_nr + 1:
            Logger.write(1, "Received out of sequence packet: " + str(pkt.seq_nr) +", next expected = " + str(self.ack_nr + 1) +". Adding to buffer")
            self.receive_pkt_buffer.append(pkt)
            return

        self.process_packet(pkt)
        while True:
            pkts = [pkt for pkt in self.receive_pkt_buffer if pkt.seq_nr == self.ack_nr + 1]
            if len(pkts) == 0:
                break
            Logger.write(1, "Picking up earlier received packet")
            self.process_packet(pkt[0])

    def process_ack(self, ack_nr):
        yet_to_ack = [p for p in self.unacked if p.seq_nr > ack_nr]
        if len(yet_to_ack) > 0:
            Logger.write(1, "Received ack, still unacked: " + ",".join([str(pkt.seq_nr) for pkt in yet_to_ack]))

        if ack_nr == self.last_received_ack and len([p for p in self.unacked if p.seq_nr == ack_nr + 1]) > 0:
            self.duplicate_acks += 1
            Logger.write(1, "Received duplicate ack")

            if self.duplicate_acks >= 3:
                # receive 3 acks for the same packet, assume the packet after that is lost; resend it
                pkt_to_resend = [p for p in self.unacked if p.seq_nr == ack_nr + 1][0]
                Logger.write(1, "Received 3 duplicates acks, resending next packet")
                self.send_packet(pkt_to_resend)
        else:
            self.unacked = [p for p in self.unacked if p.seq_nr != ack_nr]
            self.duplicate_acks = 0
        self.last_received_ack = ack_nr

    def process_packet(self, pkt):
        Logger.write(1, "Processing utp packet: " + str(pkt))
        self.ack_nr = pkt.seq_nr
        self.timestamp_dif = abs(self.time() - pkt.timestamp)
        self.other_window_size = pkt.wnd_size

        if pkt.message_type == MessageType.ST_STATE:
            self.process_ack(pkt.ack_nr)

            if self.connection_state == ConnectionState.CS_SYN_SENT:
                Logger.write(1, "Received ST_State after sending ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED
                self.ack_nr -= 1
                self.connect_event.set()

        elif pkt.message_type == MessageType.ST_DATA:
            if self.connection_state == ConnectionState.CS_SYN_RECV:
                Logger.write(1, "Received ST_Data after receiving ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED

            self.send_new_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

            self.receive_lock.acquire()
            self.receive_buffer += pkt.data
            Logger.write(1, "Added " + str(len(pkt.data)) + " bytes to receive_buffer, now " + str(len(self.receive_buffer)) + " in receive buffer")
            self.receive_lock.release()
            self.receive_event.set()

        elif pkt.message_type == MessageType.ST_SYN:
            self.connection_id = pkt.connection_id
            self.receive_connection_id = self.connection_id + 1
            self.seq_nr = random.randint(0, 65535)
            self.connection_state = ConnectionState.CS_SYN_RECV
            Logger.write(1, "Received ST_Syn; CS_SYN_RECV")
            self.send_new_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

    def time(self):
        cur_time = int(str(time.time())[-11:].replace('.', ''))
        while cur_time > 0xFFFFFFFF:
            cur_time -= 0xFFFFFFFF
        return cur_time

