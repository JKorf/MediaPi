from threading import Lock

import math

from Shared.Logger import Logger
from TorrentSrc.Streaming.StreamManager import StreamManager
from TorrentSrc.Util.Enums import OutputMode
from TorrentSrc.Util.Util import calculate_file_hash_torrent


class TorrentOutputManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces_to_output = []
        self.__lock = Lock()
        if self.torrent.output_mode == OutputMode.File:
            self.output_writer = DiskWriter(self.torrent)
        else:
            self.output_writer = StreamManager(self.torrent)

    def add_piece_to_output(self, piece):
        self.__lock.acquire()
        self.pieces_to_output.append(piece)
        self.__lock.release()

    def flush(self):
        self.update()

    def update(self):
        self.__lock.acquire()
        to_write = list(self.pieces_to_output)
        if len(to_write) == 0:
            self.__lock.release()
            return True

        self.pieces_to_output.clear()
        self.__lock.release()

        Logger.write(2, str(len(to_write)) + ' pieces done')

        for item in to_write:
            self.torrent.peer_manager.piece_done(item.index)
            self.output_writer.write_piece(item)

            # Check if first and last piece(s) are done to calculate the hash
            self.check_stream_file_hash()

        return True

    def check_stream_file_hash(self):
        if self.torrent.output_mode == OutputMode.File:
            return

        if self.torrent.stream_file_hash is not None:
            return

        start_piece = self.torrent.data_manager.pieces[self.torrent.media_file.start_piece(self.torrent.data_manager.piece_length)]
        end_piece = self.torrent.data_manager.pieces[self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length)]
        start_done = False
        end_done = False

        if start_piece.length < 65536:
            if start_piece.done and self.torrent.outputdata_manager.pieces[self.torrent.media_file.start_piece(self.torrent.data_manager.piece_length) + 1].done:
                start_done = True
        else:
            if start_piece.done:
                start_done = True

        if end_piece.start_byte - self.torrent.media_file.end_byte < 65536:
            if end_piece.done and self.torrent.data_manager.pieces[self.torrent.media_file.end_piece(self.torrent.data_manager.piece_length) - 1].done:
                end_done = True
        else:
            if end_piece.done:
                end_done = True

        if start_done and end_done:
            calculate_file_hash_torrent(self.torrent)

    def stop(self):
        self.output_writer.stop()


class DiskWriter:

    def __init__(self, torrent):
        self.torrent = torrent

    def write_piece(self, piece):
        total_written = 0
        piece_start_byte = piece.start_byte
        data = piece.get_data_and_clear()
        Logger.write(2, "Writing piece " + str(piece.index))

        while total_written < piece.length:
            file_to_write = self.get_file_for_byte(piece_start_byte + total_written)
            this_write = file_to_write.write(piece_start_byte + total_written - file_to_write.start_byte, data)
            total_written += this_write
            data = data[this_write:len(data)]

        Logger.write(2, "Piece written " + str(piece.index))

    def get_file_for_byte(self, byt):
        for file in self.torrent.files:
            if file.start_byte <= byt and file.end_byte > byt:
                return file

        return None

    def stop(self):
        pass

