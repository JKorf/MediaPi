import os
import socket

import re

from MediaPlayer.Util import Network
from MediaPlayer.Util.Network import read_ushort


def get_file_info(filename):
    with open(filename, "rb") as f:
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
    result = bytearray(socket.inet_aton(ip)) + bytearray(2)
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


def check_bytes_length(byte_data, expected):
    if byte_data is None or len(byte_data) is not expected:
        return False
    return True


def check_minimal_bytes_length(byte_data, minimal):
    if byte_data is None or len(byte_data) < minimal:
        return False
    return True


def try_parse_season_episode(path):
    path = path.lower()
    season_number = 0
    epi_number = 0

    matches = re.findall("\d+[x]\d+", path)  # 7x11
    if len(matches) > 0:
        match = matches[-1]
        season_epi = re.split("x", match)
        if len(season_epi) == 2:
            season_number = int(season_epi[0])
            epi_number = int(season_epi[1])

    if season_number == 0:
        matches = re.findall("[s][0]\d+", path)  # s01
        if len(matches) > 0:
            match = matches[-1]
            season_number = int(match[1:])

    if season_number == 0:
        matches = re.findall("[s]\d+", path)  # s1
        if len(matches) > 0:
            match = matches[-1]
            season_number = int(match[1:])

    if season_number == 0:
        if "season" in path:
            season_index = path.rfind("season") + 6  # season 1
            season_number = try_parse_number(path[season_index: season_index + 3])

    if epi_number == 0:
        matches = re.findall("[e][0]\d+", path)  # e01
        if len(matches) > 0:
            match = matches[-1]
            epi_number = int(match[1:])

    if epi_number == 0:
        matches = re.findall("[e]\d+", path)  # e1
        if len(matches) > 0:
            match = matches[-1]
            epi_number = int(match[1:])

    if epi_number == 0:
        if "episode" in path:
            epi_index = path.rfind("episode") + 7  # episode 1
            epi_number = try_parse_number(path[epi_index: epi_index + 3])

    return season_number, epi_number


def try_parse_number(number_string):
    if number_string.isdigit():
        return int(number_string)

    if len(number_string) > 1:
        if number_string[0: 2].isdigit():
            return int(number_string[0: 2])
        if number_string[1: 3].isdigit():
            return int(number_string[1: 3])
    if number_string[0].isdigit():
        return int(number_string[0])
    if number_string[1].isdigit():
        return int(number_string[1])
    return 0


def is_media_file(path):
    if "." not in path:
        return False

    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp4" or ext == ".mkv" or ext == ".avi":
        return True
