import os

from MediaPlayer.Torrents.TorrentManager import TorrentManager


class TorrentCacheManager(TorrentManager):

    def __init__(self, torrent):
        super().__init__(torrent, "cache")
        self.cache_file = None
        self.piece_length = 0
        self.total_length = 0
        self.media_start_byte = 0
        self.media_start_piece_offset = 0
        self.path = os.getcwd() + '\\Solution\\cache.tmp'

        self.bytes_written = 0

    def init(self, piece_length, total_length, media_start_byte):
        self.remove_cache_file()

        # Have to open and close it to create the file and prevent not found exception when also trying to read
        self.cache_file = open(self.path, "a+b")
        self.cache_file.close()

        self.cache_file = open(self.path, "r+b")
        self.cache_file.truncate(total_length)
        self.piece_length = piece_length
        self.total_length = total_length
        self.media_start_byte = media_start_byte
        self.media_start_piece_offset = self.media_start_byte % self.piece_length

    def read_bytes(self, start_byte, length):
        self.cache_file.seek(start_byte, 0)
        return self.cache_file.read(length)

    def write_piece(self, piece):
        start_byte = piece.start_byte - self.media_start_byte
        data = piece.get_data()
        if piece.start_byte < self.media_start_byte:
            data = data[self.media_start_piece_offset:]
            start_byte = 0

        self.cache_file.seek(start_byte, 0)
        self.cache_file.write(data)
        self.cache_file.flush()
        piece.written = True
        self.bytes_written += len(data)
        piece.clear()

    def remove_cache_file(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def stop(self):
        if self.cache_file:
            self.cache_file.close()
        self.remove_cache_file()
        super().stop()
