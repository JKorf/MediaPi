import os
from threading import Lock

from pympler import asizeof

from MediaPlayer.Streaming.StreamManager import StreamManager
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import write_size


class TorrentOutputManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces_to_output = []
        self.__lock = Lock()
        self.file_writer = DiskWriter(self.torrent)
        self.stream_manager = StreamManager(self.torrent)
        self.broadcasted_hash_data = False

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(LogVerbosity.Important, "       Size of " + str(key) + ": " + write_size(size))

    def add_piece_to_output(self, piece):
        with self.__lock:
            self.pieces_to_output.append(piece)

    def flush(self):
        self.update()

    def update(self):
        with self.__lock:
            to_write = list(self.pieces_to_output)
            if len(to_write) == 0:
                return True

            self.pieces_to_output.clear()

        Logger().write(LogVerbosity.Info, str(len(to_write)) + ' pieces done')

        self.torrent.peer_manager.pieces_done(to_write)
        self.stream_manager.write_pieces(to_write)

        if not self.broadcasted_hash_data:
            # Check if first and last piece(s) are done to calculate the hash
            self.check_stream_file_hash()

        return True

    def check_stream_file_hash(self):
        if self.torrent.stream_file_hash is not None:
            return

        start_piece = self.torrent.data_manager.get_piece_by_index(self.torrent.media_file.start_piece(self.torrent.data_manager.piece_length))
        end_piece = self.torrent.data_manager.get_piece_by_index(self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length))
        start_done = False
        end_done = False

        if start_piece.length < 65536:
            if start_piece.done and self.torrent.outputdata_manager.get_piece_by_index(self.torrent.media_file.start_piece(self.torrent.data_manager.piece_length) + 1).done:
                start_done = True
        else:
            if start_piece.done:
                start_done = True

        if self.torrent.media_file.end_byte - end_piece.start_byte < 65536:
            if end_piece.done and self.torrent.data_manager.get_piece_by_index(self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length) - 1).done:
                end_done = True
        else:
            if end_piece.done:
                end_done = True

        if start_done and end_done:
            self.broadcasted_hash_data = True
            self.torrent.media_file.first_64k = self.torrent.get_data_bytes_for_hash(0, 65536)
            self.torrent.media_file.last_64k = self.torrent.get_data_bytes_for_hash(self.torrent.media_file.length - 65536, 65536)

    def stop(self):
        self.stream_manager.stop()
        self.torrent = None


class DiskWriter:

    def __init__(self, torrent):
        self.torrent = torrent

    def write_piece(self, piece):
        total_written = 0
        piece_start_byte = piece.start_byte
        data = piece.get_data_and_clear()
        Logger().write(LogVerbosity.Debug, "Writing piece " + str(piece.index))

        while total_written < piece.length:
            file_to_write = self.get_file_for_byte(piece_start_byte + total_written)
            this_write = file_to_write.write(piece_start_byte + total_written - file_to_write.start_byte, data)
            total_written += this_write
            data = data[this_write:len(data)]

        Logger().write(LogVerbosity.Debug, "Piece written " + str(piece.index))

    def get_file_for_byte(self, byt):
        for file in self.torrent.files:
            if file.start_byte <= byt < file.end_byte:
                return file

        return None
