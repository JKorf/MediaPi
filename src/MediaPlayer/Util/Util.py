import os
import socket
import time

from MediaPlayer.Util import Network
from MediaPlayer.Util.Network import read_ushort


def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default


def get_first_x(iterable, amount, default=[]):
    result = []
    done = 0
    if iterable:
        for item in iterable:
            result.append(item)
            done += 1
            if done == amount:
                return result

        return result
    return default


def get_file_info(filename):
    f = open(filename, "rb")
    first = f.read(65536)
    f.seek(-65536, os.SEEK_END)
    last = f.read(65536)
    return os.path.getsize(filename), first, last


def uri_to_bytes(uri):
    uri_port = uri.split(':')
    result = socket.inet_aton(uri_port[0]) + bytearray(2)
    Network.write_ushort(result, int(uri_port[1]), 4)
    return result


def ip_port_to_bytes(ip, port):
    result = socket.inet_aton(ip) + bytearray(2)
    Network.write_ushort(result, port, 4)
    return result


def ip_port_from_bytes(data):
    ip = socket.inet_ntop(socket.AF_INET, data[0: 4])
    offset, port = read_ushort(data, 4)
    return ip, port


def ip_port_from_bytes_multiple(data):
    result = []
    for i in range(int(len(data) / 6)):
        result.append(ip_port_from_bytes(data[i*6: i*6 + 6]))
    return result


def uri_from_bytes(data):
    ip = socket.inet_ntop(socket.AF_INET, data[0: 4])
    offset, port = read_ushort(data, 4)
    return 'tcp://' + ip + ":" + str(port)


def check_bytes_length(bytes, expected):
    if bytes is None or len(bytes) is not expected:
        return False
    return True


def check_minimal_bytes_length(bytes, minimal):
    if bytes is None or len(bytes) < minimal:
        return False
    return True
