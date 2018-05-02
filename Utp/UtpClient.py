import random
import socket
import threading
import time
from time import sleep

from Shared.Logger import Logger
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

        self.connection_state = ConnectionState.CS_INITIAL

        self.connection_id = random.randint(0, 65535)
        self.receive_connection_id = self.connection_id + 1

        self.seq_nr = random.randint(0, 65535)
        self.ack_nr = 0
        self.timestamp_dif = 0

        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.unacked = []

        self.receive_pkt_buffer = [] # holds packages until the can be re-assembled in order
        self.receive_buffer = bytes() # received data buffer
        self.receive_thread = None
        self.send_thread = None

        self.send_buffer = bytes()
        self.__send_lock = threading.Lock()

        self.connect_event = threading.Event()
        self.receive_event = threading.Event()

    def connect(self, host=None, port=0, timeout=5):
        self.socket.bind(('', 0))
        if host is not None:
            self.host = host
        if port is not 0:
            self.port = port
        if self.port == 0:
            self.port = 6881
        self.running = True
        self.connection_state = ConnectionState.CS_SYN_SENT
        self.__start_loops()
        self.send_packet(UtpPacket(MessageType.ST_SYN, 1, 0, self.connection_id, 0, 0, 0, 0, 0))
        return self.connect_event.wait(timeout)

    def listen(self, port):
        self.socket.bind(('0.0.0.0', port))
        self.running = True
        self.__start_loops()

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
        self.socket.close()

    def __start_loops(self):
        self.receive_thread = threading.Thread(target=self.receive_loop)
        self.receive_thread.start()
        self.send_thread = threading.Thread(target=self.send_loop)
        self.send_thread.start()

    def receive_loop(self):
        while self.running:
            if len(self.receive_buffer) > 1000000: # TODO what is correct limit?
                sleep(0.01)
                continue

            pkt = self.receive_packet()
            if pkt is None:
                break

            self.handle_packet(pkt)

    def send_loop(self):
        while self.running:
            if len(self.send_buffer) == 0 or len(self.send_buffer) > 65535: # TODO what is correct limit?
                sleep(0.01)
                continue

            if len(self.send_buffer) > self.send_packet_size:
                to_send = self.send_buffer[0:self.send_packet_size]
                self.send_buffer = self.send_buffer[self.send_packet_size:]
            else:
                to_send = self.send_buffer
                self.send_buffer = bytes()

            self.send_packet(UtpPacket(MessageType.ST_DATA, 1, 0, self.receive_connection_id, 0, 0, 0, 0, 0, to_send))

    def send_packet(self, packet):
        self.__send_lock.acquire()

        if packet.data is not None or packet.message_type == MessageType.ST_SYN:
            self.seq_nr += 1 # TODO should we up this for all package or only for data?
            self.unacked.append(packet)

        packet.timestamp = self.time()
        packet.ack_nr = self.ack_nr
        packet.seq_nr = self.seq_nr
        packet.wnd_size = 65535 - sum(pkt.length for pkt in self.unacked)
        packet.timestamp_dif = 0 #self.timestamp_dif

        Logger.write(1, "Sending utp packet: " + str(packet))
        self.socket.sendto(packet.to_bytes(), (self.host, self.port))

        self.__send_lock.release()

    def receive_packet(self):
        try:
            data, address = self.socket.recvfrom(self.receive_packet_size)
        except Exception as e:
            Logger.write(1, "Receive packet ex: " + str(e))
            return None

        if self.host is None:
            self.host = address[0]
            self.port = address[1]
            Logger.write(1, "Received packet from new client at " + str(self.host) + ":" + str(self.port))
        return UtpPacket.from_bytes(data)

    def handle_packet(self, pkt):
        Logger.write(1, "Received utp packet: " + str(pkt))
        if self.connection_state != ConnectionState.CS_INITIAL and pkt.connection_id != self.connection_id and pkt.connection_id != self.receive_connection_id:
            Logger.write(1, "Unexpected connection_id: " + str(pkt.connection_id) + ", expected: " + str(self.connection_id))

        if self.ack_nr != 0:
            if (pkt.data is not None and pkt.seq_nr != self.ack_nr + 1)\
            or (pkt.data is None and pkt.seq_nr != self.ack_nr):
                self.receive_pkt_buffer.append(pkt)
                Logger.write(1, "Received out of order packet, put in in receive buffer for later. SeqNr: " + str(pkt.seq_nr) +", our AckNr: " + str(self.ack_nr))
                return

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
                self.connect_event.set()

        elif pkt.message_type == MessageType.ST_DATA:
            if self.connection_state == ConnectionState.CS_SYN_RECV:
                Logger.write(1, "Received ST_Data after receiving ST_Syn; CS_CONNECTED")
                self.connection_state = ConnectionState.CS_CONNECTED

            self.send_packet(UtpPacket(MessageType.ST_STATE, 1, 0, pkt.connection_id, 0, 0, 0, 0, 0))

            self.receive_buffer += pkt.data
            self.receive_event.set()

        elif pkt.message_type == MessageType.ST_SYN:
            self.connection_id = pkt.connection_id
            self.receive_connection_id = self.connection_id + 1
            self.seq_nr = random.randint(0, 65535)
            self.connection_state = ConnectionState.CS_SYN_RECV
            Logger.write(1, "Received ST_Syn; CS_SYN_RECV")
            self.send_packet(UtpPacket(MessageType.ST_STATE, 1, 0, pkt.connection_id, 0, 0, 0, 0, 0))
            # self.seq_nr += 1 # TODO needed?

    def time(self):
        cur_time = int(str(time.time())[-11:].replace('.', ''))
        while cur_time > 0xFFFFFFFF:
            cur_time -= 0xFFFFFFFF
        return cur_time


def start_server():
    server = UtpClient()
    server.listen(50011)
    Logger.write(1, "server started")
    while True:
        data = server.receive(50)
        Logger.write(1, "Server received: " + str(data))
        server.write(data)


#https://github.com/basarevych/utp-punch/blob/master/connection.js
#
# Logger.set_log_level(1)
# Logger.write(1, "Init")
# thread = threading.Thread(target=start_server)
# thread.daemon = True
# thread.start()
# sleep(1)
# client = UtpClient()
# suc = client.connect("localhost", 50011, 5)
# Logger.write(2, "Connect result: " + str(suc))
# sleep(1)
# data = b"Test data"
# while True:
#     client.write(data)
#     data = client.receive(4)
#     data2 = client.receive(5)
#     data = data + data2
#     Logger.write(1, "Client received echo: " + str(data))
#     sleep(1)

