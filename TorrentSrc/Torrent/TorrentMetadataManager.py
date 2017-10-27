import math
from threading import Lock

from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Bencode import bdecode


class TorrentMetadataManager:

    def __init__(self, torrent):
        self.torrent = torrent

        self.current_total_size = 0
        self.total_size_sets = dict()

        self.total_blocks = 0
        self.__lock = Lock()
        self.metadata_done = False
        self.metadata_blocks = []
        self.metadata_block_size = Settings.get_int("metadata_block_size")

    # Metadata size that is communicated doesn't seem to be very reliable, check for the most communicated size
    def set_total_size(self, size):
        if size <= 1:
            Logger.write(2, "Invalid metadata size: " + str(size))
            return

        if str(size) in self.total_size_sets:
            self.total_size_sets[str(size)] += 1
        else:
            self.total_size_sets[str(size)] = 1

        prob_size = self.get_probable_size()
        if prob_size == self.current_total_size:
            # Nothing changed
            return

        if len(self.metadata_blocks) > 0:
            self.metadata_blocks.clear()
            Logger.write(2, "Metadata size reset. ")
            for key, value in self.total_size_sets.items():
                Logger.write(2, "size " + key + ": " + str(value) + "x")

        # New total size determined
        self.current_total_size = size
        blocks = int(math.ceil(self.current_total_size / self.metadata_block_size))
        Logger.write(2, "Metadata new size set to " + str(self.current_total_size) + " ( " + str(blocks) + " blocks )")

        for index in range(blocks):
            self.metadata_blocks.append(MetadataBlock(index, min(self.current_total_size - (index * self.metadata_block_size), self.metadata_block_size)))

    def get_probable_size(self):
        max = (None, 0)
        for key, value in self.total_size_sets.items():
            if value > max[1]:
                max = (key, value)
        return int(max[0])

    def add_metadata_piece(self, index, data):
        self.__lock.acquire()
        if self.metadata_done:
            self.__lock.release()
            return

        if index >= len(self.metadata_blocks) or index < 0:
            Logger.write(2, 'Invalid metadata block index: ' + index)
            self.__lock.release()
            return

        if data is None or len(data) == 0:
            Logger.write(2, 'Invalid metadata block data')
            self.__lock.release()
            return

        self.metadata_blocks[index].write(data)

        if len([x for x in self.metadata_blocks if not x.done]) == 0:
            Logger.write(2, "Metadata done")
            self.metadata_done = True

            data = bytearray(self.current_total_size)
            for block in self.metadata_blocks:
                data[self.metadata_block_size * block.index:] = block.data

            data = bdecode(bytes(data))
            self.torrent.parse_info_dictionary(data)
            self.metadata_blocks.clear()
        self.__lock.release()

    def get_pieces_to_do(self):
        return [x for x in self.metadata_blocks if not x.done]


class MetadataBlock:

    def __init__(self, index, length):
        self.index = index
        self.length = length
        self.data = None
        self.done = False

    def write(self, data):
        self.data = data
        self.done = True
