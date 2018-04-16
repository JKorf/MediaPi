import os
import socket
import time
import struct

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from TorrentSrc.Util import Network
from TorrentSrc.Util.Network import read_ushort


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


def calculate_file_hash_torrent(torrent):
    longlongformat = '<q'
    bytesize = struct.calcsize(longlongformat)

    hash = torrent.media_file.length
    first_64 = torrent.get_data_bytes_for_hash(0, 65536)
    last_64 = torrent.get_data_bytes_for_hash(torrent.media_file.length - 65536, 65536)

    for x in range(int(65536 / bytesize)):
        (l_value,) = struct.unpack_from(longlongformat, first_64, x * bytesize)
        hash += l_value
        hash &= 0xFFFFFFFFFFFFFFFF

    for x in range(int(65536 / bytesize)):
        (l_value,) = struct.unpack_from(longlongformat, last_64, x * bytesize)
        hash += l_value
        hash &= 0xFFFFFFFFFFFFFFFF

    torrent.stream_file_hash = "%016x" % hash
    EventManager.throw_event(EventType.StreamFileHashKnown, [torrent.media_file.length, torrent.stream_file_hash])


def calculate_file_hash_file(file, throw_event=True):
    longlongformat = '<q'  # little-endian long long
    bytesize = struct.calcsize(longlongformat)

    f = open(file, "rb")

    filesize = os.path.getsize(file)
    hash = filesize

    if filesize < 65536 * 2:
        return "SizeError"

    for x in range(int(65536 / bytesize)):
        buffer = f.read(bytesize)
        (l_value,) = struct.unpack(longlongformat, buffer)
        hash += l_value
        hash = hash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

    f.seek(max(0, filesize - 65536), 0)
    for x in range(int(65536 / bytesize)):
        buffer = f.read(bytesize)
        (l_value,) = struct.unpack(longlongformat, buffer)
        hash += l_value
        hash = hash & 0xFFFFFFFFFFFFFFFF

    f.close()
    returnedhash = "%016x" % hash
    if throw_event:
        EventManager.throw_event(EventType.StreamFileHashKnown, [filesize, returnedhash])
    return filesize, returnedhash


def write_size(data):
    if data < 1100:
        return str(data) + 'kb'
    if data < 1100000:
        return str(round(data / 1000, 2)) + 'kb'
    if data < 1100000000:
        return str(round(data / 1000000, 2)) + 'mb'
    if data < 1100000000000:
        return str(round(data / 1000000000, 2)) + 'gb'
    else:
        return str(round(data / 1000000000, 2)) + 'tb'


def write_time_from_seconds(t):
    return time.strftime('%H:%M:%S', time.gmtime(t))


def uri_to_bytes(uri):
    result = bytearray(6)

    uri_port = uri.split(':')
    split = uri_port[0].split('.')
    if len(split) < 4:
        return None

    result[0] = int(split[0])
    result[1] = int(split[1])
    result[2] = int(split[2])
    result[3] = int(split[3])

    Network.write_ushort(result, int(uri_port[1]), 4)
    return result


def ip_port_to_bytes(ip, port):
    result = bytearray(6)

    split = ip.split('.')
    if len(split) < 4:
        return None

    result[0] = int(split[0])
    result[1] = int(split[1])
    result[2] = int(split[2])
    result[3] = int(split[3])

    Network.write_ushort(result, port, 4)
    return result


def ip_port_from_bytes(data):
    ip = socket.inet_ntop(socket.AF_INET, data[0: 4])
    # offset, ip = read_bytes(data, 4, offset)
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


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}
