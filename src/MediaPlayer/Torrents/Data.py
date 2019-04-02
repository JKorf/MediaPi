import math
from threading import Lock

from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings


class Bitfield(LogObject):
    def __init__(self, parent, size):
        super().__init__(parent, "bitfield")
        self.size = size
        self.field = [False] * size

        self.pieces_has_log = 0

    @property
    def has_all(self):
        return self.field.count(True) == self.size

    @property
    def has_none(self):
        return self.field.count(False) == self.size

    def update_piece(self, index, value):
        self.field[index] = value
        self.pieces_has_log += 1

    def has_piece(self, index):
        return self.field[index]

    def set_has_all(self):
        for i in range(self.size):
            self.field[i] = True
        self.pieces_has_log = self.size

    def set_has_none(self):
        for i in range(self.size):
            self.field[i] = False
        self.pieces_has_log = 0

    def update(self, data):
        self.pieces_has_log = 0
        for i in range(self.size):
            byte_index = i // 8
            bit_index = i % 8

            if ((data[byte_index] << bit_index) & 0x80) == 0x80:
                self.field[i] = True
                self.pieces_has_log += 1
            else:
                self.field[i] = False

    def get_bitfield(self):
        result = bytearray(math.ceil(self.size / 8))
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


class Block(LogObject):
    def __init__(self, parent, index, piece_index, block_index_in_piece, start_byte_in_piece, start_byte_total, length):
        super().__init__(parent, "Block " + str(index))
        self.index = index
        self.piece_index = piece_index
        self.block_index_in_piece = block_index_in_piece
        self.start_byte_in_piece = start_byte_in_piece
        self.start_byte_total = start_byte_total
        self.length = length
        self.done = False
        self.data = None

        self.peers_downloading = []
        self.peers_downloading_log = ""

    def _write_data(self, data):
        Logger().write(LogVerbosity.All, "Writing block " + str(self.index) + " in piece " + str(self.piece_index))
        self.data = data
        self.done = True

    def clear(self):
        self.data = None

    def add_downloader(self, peer):
        self.peers_downloading.append(peer)
        self.peers_downloading_log = ", ".join([str(x.id) for x in self.peers_downloading])

    def remove_downloader(self, peer):
        self.peers_downloading.remove(peer)
        self.peers_downloading_log = ", ".join([str(x.id) for x in self.peers_downloading])


class Piece(LogObject):
    @property
    def blocks(self):
        if not self.initialized:
            self.init_blocks()
            self.initialized = True
        return self._blocks

    def __init__(self, parent, index, block_start_index, start_byte, length, persistent):
        super().__init__(parent, "piece " + str(index))

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

    def init_blocks(self):
        Logger().write(LogVerbosity.Debug, "Initializing blocks for piece " + str(self.index))
        self._blocks = dict()
        partial_block = self.length % self.block_size
        whole_blocks = int(math.floor(self.length / self.block_size))
        for index in range(whole_blocks):
            self._blocks[index] = Block(self, self.block_start_index + index, self.index, index, index * self.block_size,
                                       self.start_byte + (index * self.block_size), self.block_size)
        if partial_block != 0:
            self._blocks[len(self._blocks)] = Block(self, self.block_start_index + len(self._blocks), self.index, len(self._blocks),
                                                  len(self._blocks) * self.block_size, self.start_byte + (len(self._blocks) * self.block_size), partial_block)
        self.total_blocks = len(self._blocks)

    def get_block_by_offset(self, offset_in_piece):
        if self.cleared:
            raise Exception("Trying to retrieve block of cleared piece")

        index = int(math.floor(offset_in_piece / self.block_size))
        return self.blocks.get(index)

    def write_block(self, block, data):
        if self.done:
            return False

        block._write_data(data)
        self.block_writes += 1
        if self.block_writes >= self.total_blocks:
            if len([x for x in self.blocks.values() if not x.done]) == 0:
                self.done = True
                Logger().write(LogVerbosity.Debug, "Piece " + str(self.index) + " done after writing block " + str(block.index))

                self._data = bytearray()
                for block in self.blocks.values():
                    if self._data is None or block.data is None:
                        raise Exception("Erased data on piece " + str(self.index) + ", block: " + str(block.index))
                    self._data.extend(block.data)
                return True
        return False

    def get_data(self):
        if not self.done:
            return None

        if self.cleared or self._data is None:
            raise Exception("Trying to retrieve cleared piece")

        return self._data

    def clear(self):
        if self.persistent:
            raise Exception("Can't clear persistent pieces")

        self._blocks = dict()
        self.cleared = True
        self._data = None
        Logger().write(LogVerbosity.Debug, "Piece " + str(self.index) + " cleared")

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
