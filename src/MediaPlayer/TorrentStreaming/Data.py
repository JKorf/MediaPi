import math
from threading import Lock

import sys

from Shared.Logger import Logger
from Shared.Settings import Settings


class Bitfield:
    def __init__(self, size):
        self.size = size
        self.field = [False] * size

    @property
    def has_all(self):
        return self.field.count(True) == self.size

    @property
    def has_none(self):
        return self.field.count(False) == self.size

    def update_piece(self, index, value):
        self.field[index] = value

    def has_piece(self, index):
        return self.field[index]

    def set_has_all(self):
        for i in range(self.size):
            self.field[i] = True

    def set_has_none(self):
        for i in range(self.size):
            self.field[i] = False

    def update(self, data):
        for i in range(self.size):
            byte_index = i // 8
            bit_index = i % 8

            if ((data[byte_index] << bit_index) & 0x80) == 0x80:
                self.field[i] = True
            else:
                self.field[i] = False

    def get_bitfield(self):
        result = bytearray(int(round(self.size / 8, 0)))
        for index in range(self.size):
            for byte_index in range(8):
                mask = 1 << byte_index
                current = (index * 8) + byte_index
                if current >= self.size:
                    continue

                if self.has_piece(current):
                    result[index] |= mask

        return result

    def interested_in(self, bitfield):
        for index in range(self.size):
            if not self.field[index] and bitfield.field[index]:
                return True
        return False


class Block:
    def __init__(self, index, piece_index, block_index_in_piece, start_byte_in_piece, start_byte_total, length):
        self.index = index
        self.piece_index = piece_index
        self.block_index_in_piece = block_index_in_piece
        self.start_byte_in_piece = start_byte_in_piece
        self.start_byte_total = start_byte_total
        self.length = length
        self.done = False
        self.data = None

        self.download_lock = Lock()
        self.peers_downloading = []

    def _write_data(self, data):
        self.data = data
        self.done = True

    def clear(self):
        self.data = None

    def add_downloader(self, peer):
        with self.download_lock:
            self.peers_downloading.append(peer)

    def remove_downloader(self, peer):
        with self.download_lock:
            self.peers_downloading.remove(peer)


class Piece:
    @property
    def blocks(self):
        if not self.initialized:
            self.init_blocks()
            self.initialized = True
        return self._blocks

    def __init__(self, index, block_start_index, start_byte, length, persistent):
        self.index = index
        self.block_start_index = block_start_index
        self.start_byte = start_byte
        self.end_byte = start_byte + length
        self.length = length
        self.done = False
        self.cleared = False

        self._data = None
        self._blocks = dict()
        self.initialized = False

        self.validated = False
        self.block_writes = 0
        self.total_blocks = 0
        self.block_size = Settings.get_int("block_size")
        self.priority = 0
        self.persistent = persistent

        self.write_lock = Lock()

    def init_blocks(self):
        self._blocks = dict()
        partial_block = self.length % self.block_size
        whole_blocks = int(math.floor(self.length / self.block_size))
        for index in range(whole_blocks):
            self._blocks[index] = Block(self.block_start_index + index, self.index, index, index * self.block_size,
                                       self.start_byte + (index * self.block_size), self.block_size)
        if partial_block != 0:
            self._blocks[len(self._blocks)] = Block(self.block_start_index + len(self._blocks), self.index, len(self._blocks),
                                                  len(self._blocks) * self.block_size, self.start_byte + (len(self._blocks) * self.block_size), partial_block)
        self.total_blocks = len(self._blocks)

    def get_block_by_offset(self, offset_in_piece):
        index = int(math.floor(offset_in_piece / self.block_size))
        return self.blocks.get(index)

    def write_block(self, block, data):
        with self.write_lock:
            if self.done:
                return False

            block._write_data(data)
            self.block_writes += 1
            if self.block_writes >= self.total_blocks:
                if len([x for x in self.blocks.values() if not x.done]) == 0:
                    self.done = True
                    return True
            return False

    def get_data(self):
        if not self.done:
            return None

        if self.cleared:
            raise Exception("Trying to retrieve cleared piece")

        if self._data is None:
            self._data = bytearray()
            for block in self.blocks.values():
                if self._data is None or block.data is None:
                    raise Exception("Erased data on piece " + str(self.index) + ", block: " + str(block.index) )
                self._data.extend(block.data)
        return self._data

    def clear(self):
        if self.persistent:
            raise Exception("Can't clear persistent pieces")

        for block in self._blocks.values():
            block.clear()
        self.cleared = True
        self._data = None

    def reset(self):
        self.block_writes = 0
        for block in self._blocks.values():
            block.clear()
            block.done = False
        self.done = False
        self._data = None
        self.validated = False
        self.cleared = False

    def get_data_and_clear(self):
        data = self.get_data()
        self.clear()
        return data
