import math

from Shared.Logger import Logger
from Shared.Settings import Settings


class StreamPrioritizer:

    def __init__(self, torrent):
        self.torrent = torrent
        self.init_done = False
        self.start_piece = 0
        self.end_piece = 0
        self.stream_end_buffer_pieces = 0
        self.stream_play_buffer_high_priority = 0
        self.subtitle_pieces = []

    def prioritize_piece_index(self, piece_index):
        if not self.init_done:
            self.init_done = True
            self.start_piece = int(math.floor(self.torrent.media_file.start_byte / self.torrent.piece_length))
            self.end_piece = int(math.floor(self.torrent.media_file.end_byte / self.torrent.piece_length))
            self.stream_end_buffer_pieces = self.torrent.data_manager.get_piece_by_offset(self.torrent.media_file.end_byte - Settings.get_int("stream_end_buffer")).index
            self.stream_play_buffer_high_priority = max(1500000 // self.torrent.piece_length, 2) # TODO setting

            for sub in self.torrent.subtitles:
                start_piece = self.torrent.data_manager.get_piece_by_offset(sub.start_byte).index
                end_piece = self.torrent.data_manager.get_piece_by_offset(sub.end_byte).index
                for i in range(start_piece, end_piece + 1):
                    if i not in self.subtitle_pieces:
                        self.subtitle_pieces.append(i)

        if piece_index in self.subtitle_pieces:
            return 100

        if piece_index < self.start_piece or piece_index > self.end_piece:
            return 0

        dif = piece_index - self.torrent.stream_position

        if dif < 0:
            return 0

        if piece_index >= self.stream_end_buffer_pieces:
            return 99

        if piece_index == self.start_piece:
            return 101

        if self.torrent.end_game:
            return 100

        if dif <= self.stream_play_buffer_high_priority:
            return 100

        dif_bytes = dif*self.torrent.piece_length
        return max(10, 100 - (dif_bytes / 1000 / 1000))


class FilePrioritizer:

    def __init__(self, torrent):
        self.torrent = torrent

    def prioritize_piece_index(self, piece_index):
        if self.torrent.end_game:
            return 100

        return 90
