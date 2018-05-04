import socket

from Shared.Logger import Logger
from Utp.UtpObjects import UtpPacket


class UtpConnection:

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = host
        self.port = port
        self.packet_send_queue = []

    def send(self, pkt):
        if not isinstance(pkt, UtpPacket):
            raise Exception("Send is not a packet")
        self.packet_send_queue.append(pkt)

    def flush(self):
        while len(self.packet_send_queue) > 0:
            pkt = self.packet_send_queue.pop(0)
            Logger.write(1, "Sending pkt " + str(pkt))
            self.socket.sendto(pkt.to_bytes(), (self.host, self.port))

    def receive(self):
        data, addr = self.socket.recvfrom(1400)
        return data