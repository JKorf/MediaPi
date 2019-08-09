import os

from MediaPlayer.Torrents.TorrentManager import TorrentManager


class TorrentCacheManager(TorrentManager):

    def __init__(self, torrent):
        super().__init__(torrent, "cache")
        self.open_cache_files = []
        self.piece_length = 0
        self.total_length = 0
        self.media_start_byte = 0
        self.media_start_piece_offset = 0
        self.path = os.getcwd() + '\\Solution\\cache\\'

        self.bytes_written = 0

    def init(self, piece_length, total_length, media_start_byte):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        self.remove_cache_files()

        self.piece_length = piece_length
        self.total_length = total_length
        self.media_start_byte = media_start_byte
        self.media_start_piece_offset = self.media_start_byte % self.piece_length

    def read_bytes(self, start_byte, length):
        actual_start_byte = start_byte + self.media_start_byte
        pieces = self.torrent.data_manager.get_all_pieces_in_range(actual_start_byte, actual_start_byte + length)

        offset = actual_start_byte - pieces[0].start_byte
        result = bytearray()
        for piece in pieces:
            with open(self.path + str(piece.index), "rb") as data_file:
                if offset is not 0:
                    data_file.seek(offset, 0)
                result += data_file.read(self.piece_length - offset)
            offset = 0
        return result[0: length]

    def write_piece(self, piece):
        with open(self.path + str(piece.index), "ab") as data_file:
            data_file.write(piece.get_data())
        piece.written = True
        piece.clear()
        self.bytes_written += piece.length

    def remove_cache_files(self):
        for the_file in os.listdir(self.path):
            file_path = os.path.join(self.path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    def stop(self):
        self.remove_cache_files()
        super().stop()
