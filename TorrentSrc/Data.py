import math

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

    def __init__(self, index, piece_index, block_index_in_piece, start_byte_in_piece, start_byte_total, length, persistent):
        self.index = index
        self.piece_index = piece_index
        self.block_index_in_piece = block_index_in_piece
        self.start_byte_in_piece = start_byte_in_piece
        self.start_byte_total = start_byte_total
        self.length = length
        self.done = False
        self.data = None
        self.persistent = persistent

    def write_data(self, data):
        self.data = data
        self.done = True

    def clear(self):
        self.data = None


class Piece:

    def __init__(self, index, block_start_index, start_byte, length, persistent):
        self.index = index
        self.block_start_index = block_start_index
        self.start_byte = start_byte
        self.end_byte = start_byte + length
        self.length = length
        self.done = False
        self.blocks = []
        self.block_size = Settings.get_int("block_size")
        self.priority = 0
        self.persistent = persistent

        self.init_blocks()

    def init_blocks(self):
        partial_block = self.length % self.block_size
        whole_blocks = int(math.floor(self.length / self.block_size))
        for index in range(whole_blocks):
            self.blocks.append(Block(self.block_start_index + index, self.index, index, index * self.block_size,
                                     self.start_byte + (index * self.block_size), self.block_size, self.persistent))
        if partial_block != 0:
            self.blocks.append(Block(self.block_start_index + len(self.blocks), self.index, len(self.blocks),
                                     len(self.blocks) * self.block_size, self.start_byte + (len(self.blocks) * self.block_size), partial_block, self.persistent))

    def get_block_by_offset(self, offset_in_piece):
        return next((x for x in self.blocks if x.start_byte_in_piece == offset_in_piece), None)

    def write_block(self, block, data):
        block.write_data(data)
        if len([x for x in self.blocks if not x.done]) == 0:
            self.done = True

    def get_data(self):
        if not self.done:
            return None

        data = bytearray()
        for block in self.blocks:
            data.extend(block.data)
        return data

    def clear(self):
        if self.persistent:
            raise Exception("Can't clear persistent pieces")

        for block in self.blocks:
            block.clear()

    def reset(self):
        for block in self.blocks:
            block.clear()
            block.done = False
        self.done = False

    def get_data_and_clear(self):
        data = self.get_data()
        self.clear()
        return data
