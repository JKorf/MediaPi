import os
from threading import Lock

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from TorrentSrc.Streaming.StreamManager import StreamManager


class TorrentOutputManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces_to_output = []
        self.__lock = Lock()
        self.file_writer = DiskWriter(self.torrent)
        self.stream_manager = StreamManager(self.torrent)
        self.broadcasted_hash_data = False

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
            self.stream_manager.write_piece(item)

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
            EventManager.throw_event(EventType.HashDataKnown,
                                     [self.torrent.media_file.length,
                                      os.path.basename(self.torrent.media_file.path),
                                      self.torrent.get_data_bytes_for_hash(0, 65536),
                                      self.torrent.get_data_bytes_for_hash(self.torrent.media_file.length - 65536, 65536)])

    def stop(self):
        self.stream_manager.stop()


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

