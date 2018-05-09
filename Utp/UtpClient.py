import random
import threading
from datetime import datetime, timezone

from Shared.Logger import Logger
from Shared.Util import current_time
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

        self.last_send = 0
        self.epoch = datetime.utcfromtimestamp(0)
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
        self.resend_states = 0

        self.reset = False
        self.received_fin = False

        self.running = False
        self.utp_connection = UtpConnection(self.host, self.port)
        self.socket = self.utp_connection.socket
        self.unacked = []

        self.timeout = 1000
        self.rtt = 0
        self.rtt_var = 0

        self.receive_lock = threading.Lock()
        self.receive_pkt_buffer = [] # holds packages until the can be re-assembled in order
        self.receive_buffer = bytes() # received data buffer
        self.send_buffer = bytes() # send data buffer
        self.send_lock = threading.Lock()

        self.connect_event = threading.Event()

    def data_available(self):
        return len(self.receive_buffer) != 0 or self.connection_state == ConnectionState.CS_DISCONNECTED

    def connect(self, timeout=5):
        if self.port == 0:
            self.port = 6881
        self.running = True
        self.connection_state = ConnectionState.CS_SYN_SENT

        self.send_new_packet(UtpPacket(MessageType.ST_SYN, 1, 0, self.connection_id, 0, 0, 0, 0, 0))
        return self.connect_event.wait(timeout)

    def check_timeouts(self):
        if self.connection_state == ConnectionState.CS_DISCONNECTED:
            return

        check_time = self.time()
        timed_out_unacks = [pkt for pkt in self.unacked if check_time - pkt.timestamp > (pkt.resends + 1) * self.timeout]
        for pkt in timed_out_unacks:
            Logger.write(1, "Resending timed out pkt")
            pkt.resends += 1
            self.send_packet(pkt)

    def send(self, data):
        if self.connection_state == ConnectionState.CS_DISCONNECTED:
            return False

        self.send_lock.acquire()
        self.send_buffer += data
        self.send_lock.release()
        return True

    def receive_available(self, max_amount):
        if len(self.receive_buffer) == 0:
                return None

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

        self.last_send = current_time()
        self.utp_connection.flush()

    def send_new_packet(self, packet):
        if packet.data is not None or packet.message_type == MessageType.ST_SYN:
            self.seq_nr += 1
            self.unacked.append(packet)
        packet.seq_nr = self.seq_nr
        self.send_packet(packet)

    def send_packet(self, packet):
        if self.connection_state == ConnectionState.CS_DISCONNECTED:
            return

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

        if self.ack_nr != 0 and pkt.seq_nr > self.ack_nr + 1 and pkt.message_type != MessageType.ST_RESET:
            Logger.write(1, "Received out of sequence packet: " + str(pkt.seq_nr) +", next expected = " + str(self.ack_nr + 1) +". Adding to buffer")
            self.receive_pkt_buffer.append(pkt)
            return

        elif self.ack_nr != 0 and pkt.message_type == MessageType.ST_DATA and pkt.seq_nr <= self.ack_nr:
            Logger.write(1, "Received pkt we already acked: " +str(pkt.seq_nr))
            self.resend_states += 1
            self.send_new_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))
            return

        self.resend_states = 0
        self.process_packet(pkt)
        while True:
            pkts = [pkt for pkt in self.receive_pkt_buffer if pkt.seq_nr == self.ack_nr + 1]
            if len(pkts) == 0:
                break
            Logger.write(1, "Picking up earlier received packet")
            self.process_packet(pkts[0])
            self.receive_pkt_buffer.remove(pkts[0])

    def process_ack(self, ack_nr):
        acked = [pkt for pkt in self.unacked if pkt.seq_nr == ack_nr]
        if len(acked) > 0 and acked[0].resends == 0:
            acked_pkt = acked[0]
            time_passed = self.time() - acked_pkt.timestamp
            if self.rtt == 0:
                self.rtt = time_passed
            else:
                delta = self.rtt - time_passed
                self.rtt_var += (abs(delta) - self.rtt_var) / 4
                self.rtt += (time_passed - self.rtt) / 8
                self.timeout = max(self.rtt + self.rtt_var * 4, 500)
                Logger.write(1, "Setting timeout to " + str(self.timeout) + " based on rtt of " + str(self.rtt) + " and rtt_var of " + str(self.rtt_var))

        self.unacked = [pkt for pkt in self.unacked if pkt.seq_nr > ack_nr]
        yet_to_ack = [p for p in self.unacked if p.seq_nr > ack_nr]
        if len(yet_to_ack) > 0:
            Logger.write(1, "Received ack, still unacked: " + ",".join([str(pkt.seq_nr) for pkt in yet_to_ack]))
            for pkt in yet_to_ack:
                Logger.write(1, "Resending pkt not yet acked ")
                self.send_packet(pkt)

        if ack_nr == self.last_received_ack and len([p for p in self.unacked if p.seq_nr == ack_nr + 1]) > 0:
            self.duplicate_acks += 1
            Logger.write(1, "Received duplicate ack")

            if self.duplicate_acks >= 2:
                # receive 3 acks for the same packet, assume the packet after that is lost; resend it
                pkt_to_resend = [p for p in self.unacked if p.seq_nr == ack_nr + 1][0]
                Logger.write(1, "Received 3 duplicates acks, resending packet")
                self.send_packet(pkt_to_resend)
        else:
            self.unacked = [p for p in self.unacked if p.seq_nr != ack_nr]
            self.duplicate_acks = 0
        self.last_received_ack = ack_nr

    def process_packet(self, pkt):
        Logger.write(1, "Processing utp packet: " + str(pkt))
        if pkt.message_type == MessageType.ST_DATA or self.ack_nr == 0:
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
            self.process_ack(pkt.ack_nr)

            if self.connection_state == ConnectionState.CS_SYN_RECV:
                Logger.write(1, "Received ST_Data after receiving ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED

            self.send_new_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

            self.receive_lock.acquire()
            self.receive_buffer += pkt.data
            Logger.write(1, "Added " + str(len(pkt.data)) + " bytes to receive_buffer, now " + str(len(self.receive_buffer)) + " in receive buffer")
            self.receive_lock.release()

        elif pkt.message_type == MessageType.ST_SYN:
            self.connection_id = pkt.connection_id
            self.receive_connection_id = self.connection_id + 1
            self.seq_nr = random.randint(0, 65535)
            self.connection_state = ConnectionState.CS_SYN_RECV
            Logger.write(1, "Received ST_Syn; CS_SYN_RECV")
            self.send_new_packet(UtpPacket(MessageType.ST_STATE, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0))

        elif pkt.message_type == MessageType.ST_RESET:
            Logger.write(1, "Received ST_Reset; closing")
            self.connection_state = ConnectionState.CS_DISCONNECTED

        elif pkt.message_type == MessageType.ST_FIN:
            Logger.write(1, "Received ST_Fin; closing")
            self.connection_state = ConnectionState.CS_DISCONNECTED

    def time(self):
        time = int((datetime.now() - self.epoch).total_seconds() * 1000.0)
        while time > 4294967295:
            time -= 4294967295
        return time

