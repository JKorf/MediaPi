import math

from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Enums import StreamFileState


class StreamPrioritizer:

    def __init__(self, torrent):
        self.torrent = torrent
        self.init_done = False
        self.start_piece = 0
        self.end_piece = 0
        self.stream_end_buffer_pieces = 0
        self.stream_play_buffer_high_priority = 0
        self.subtitle_pieces = []
        self.max_chunk_size = Settings.get_int("max_chunk_size")

    def prioritize_piece_index(self, piece_index):
        if not self.init_done:
            self.init_done = True
            self.start_piece = self.torrent.media_file.start_piece(self.torrent.piece_length)
            self.end_piece = self.torrent.media_file.end_piece(self.torrent.piece_length)
            self.stream_end_buffer_pieces = self.torrent.data_manager.get_piece_by_offset(self.torrent.media_file.end_byte - Settings.get_int("stream_end_buffer_tolerance")).index
            self.stream_play_buffer_high_priority = max(1500000 // self.torrent.piece_length, 2) # TODO setting

        if piece_index in self.subtitle_pieces:
            return 100

        if piece_index < self.start_piece or piece_index > self.end_piece:
            return 0

        dif = piece_index - self.torrent.stream_position

        if dif < 0:
            return 0

        if piece_index <= self.start_piece + math.ceil(self.max_chunk_size / self.torrent.piece_length) or piece_index > self.end_piece - math.ceil(self.max_chunk_size / self.torrent.piece_length):
            return 101 # Highest prio on start, to be able to return the first data, and end to be able to calc hash

        if piece_index >= self.stream_end_buffer_pieces:
            return 101 - ((self.end_piece - piece_index) / 100000) # Second highest prio on start, to be able to return metadata at end of file

        if self.torrent.end_game:
            return 100

        if dif <= self.stream_play_buffer_high_priority:
            return 100

        dif_bytes = dif*self.torrent.piece_length
        return max(10, 100 - (dif_bytes / 1000 / 1000))

