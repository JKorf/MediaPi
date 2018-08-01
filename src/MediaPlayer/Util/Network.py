import struct


def write_short(buffer, short, offset):
    struct.pack_into('!h', buffer, offset, short)
    offset += 2
    return offset


def write_int(buffer, integer, offset):
    struct.pack_into('!i', buffer, offset, integer)
    offset += 4
    return offset


def write_long(buffer, long, offset):
    struct.pack_into('!q', buffer, offset, long)
    offset += 8
    return offset


def write_ushort(buffer, ushort, offset):
    struct.pack_into('!H', buffer, offset, ushort)
    offset += 2
    return offset


def write_uint(buffer, uinteger, offset):
    struct.pack_into('!I', buffer, offset, uinteger)
    offset += 4
    return offset


def write_ulong(buffer, ulong, offset):
    struct.pack_into('!Q', buffer, offset, ulong)
    offset += 8
    return offset


def write_bytes(buffer, data, offset):
    buffer[offset: offset + len(data)] = data
    offset += len(data)
    return offset


def write_int_as_byte(buffer, integer, offset):
    buffer[offset] = integer
    offset += 1
    return offset


def read_short(buffer, offset):
    short = struct.unpack_from('!h', buffer, offset)
    offset += 2
    return offset, short[0]


def read_integer(buffer, offset):
    integer = struct.unpack_from('!i', buffer, offset)
    offset += 4
    return offset, integer[0]


def read_long(buffer, offset):
    long = struct.unpack_from('!q', buffer, offset)
    offset += 8
    return offset, long[0]


def read_ushort(buffer, offset):
    ushort = struct.unpack_from('!H', buffer, offset)
    offset += 2
    return offset, ushort[0]


def read_uinteger(buffer, offset):
    uinteger = struct.unpack_from('!I', buffer, offset)
    offset += 4
    return offset, uinteger[0]


def read_ulong(buffer, offset):
    ulong = struct.unpack_from('!Q', buffer, offset)
    offset += 8
    return offset, ulong[0]


def read_bytes(buffer, length, offset):
    data = buffer[offset: offset + length]
    offset += length
    return offset, data


def read_byte_as_int(buffer, offset):
    result = int(buffer[offset])
    offset += 1
    return offset, result
