import hashlib
import math

from pympler import asizeof

from MediaPlayer.Torrents.Data import Bitfield, Piece
from MediaPlayer.Torrents.TorrentManager import TorrentManager
from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Timing import Timing
from Shared.Util import current_time, write_size


class TorrentDataManager(TorrentManager):

    def __init__(self, torrent):
        super().__init__(torrent, "data")
        self.torrent = torrent
        self._pieces = dict()
        self.init_done = False
        self.total_pieces = 0
        self.piece_length = 0
        self.bitfield = None
        self.hashes = []

        self.block_size = Settings.get_int("block_size")
        self.broadcasted_hash_data = False
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)
        self.blocks_done_length = 0
        self.last_piece_index = 0

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(LogVerbosity.Important, "       Size of " + str(key) + ": " + write_size(size))

    def check_pieces_size(self):
        Logger().write(LogVerbosity.Important, "    _pieces size: " + write_size(asizeof.asizeof(self._pieces)))
        not_done_pieces = [piece for piece in self._pieces.values() if not piece.done]
        done_pieces = [piece for piece in self._pieces.values() if piece.done]
        stream_index = [piece for piece in self._pieces.values() if piece.index < self.torrent.stream_position]
        stream_index_50_mb = [piece for piece in self._pieces.values() if piece.index > self.torrent.stream_position + (50000000 // self.piece_length)]
        Logger().write(LogVerbosity.Important, "    pieces not done: " + str(len(not_done_pieces)) + " - " + write_size(asizeof.asizeof(not_done_pieces)))
        Logger().write(LogVerbosity.Important, "    pieces done: " + str(len(done_pieces)) + " - " + write_size(asizeof.asizeof(done_pieces)))
        Logger().write(LogVerbosity.Important, "    pieces < stream index: " + str(len(stream_index)) + " - " + write_size(asizeof.asizeof(stream_index)))
        Logger().write(LogVerbosity.Important, "    pieces > stream index + 50mb: " + str(len(stream_index_50_mb)) + " - " + write_size(asizeof.asizeof(stream_index_50_mb)))
        Logger().write(LogVerbosity.Important, "    pieces with initialized blocks: " + str(len([piece for piece in self._pieces.values() if len(piece._blocks) > 0])))
        if self.torrent.stream_manager.buffer is not None:
            data_ready = [piece for piece in self.torrent.stream_manager.buffer.data_ready]
            Logger().write(LogVerbosity.Important, "    pieces in data_ready: " + str(len(data_ready)) + " - " + write_size(asizeof.asizeof(data_ready)))

    def unregister(self):
        EventManager.deregister_event(self._event_id_stopped)

    def set_piece_info(self, piece_length, piece_hashes):
        self.update_hashes(piece_hashes)
        self.piece_length = piece_length
        self.total_pieces = int(math.ceil(self.torrent.total_size / piece_length))
        self.bitfield = Bitfield(self.torrent, self.total_pieces)
        self.init_pieces()

    def init_pieces(self):
        blocks_per_piece = int(math.ceil(self.piece_length / self.block_size))

        start_piece = math.floor(self.torrent.media_file.start_byte / self.piece_length)
        end_piece = math.ceil(self.torrent.media_file.end_byte / self.piece_length)
        current_byte = start_piece * self.piece_length

        start_time = current_time()
        for index in range(end_piece - start_piece):
            piece_index = start_piece + index

            if current_byte + self.piece_length > self.torrent.total_size:
                # last piece, is not full length
                self._pieces[piece_index] = Piece(self, piece_index, piece_index * blocks_per_piece, current_byte, self.torrent.total_size - current_byte)
            else:
                self._pieces[piece_index] = Piece(self, piece_index, piece_index * blocks_per_piece, current_byte, self.piece_length)

            current_byte += self.piece_length
            self.last_piece_index = piece_index

        self.init_done = True
        Logger().write(LogVerbosity.Info, "Pieces initialized, " + str(len(self._pieces)) + " pieces created in " + str(current_time() - start_time) + "ms")

    def block_done(self, peer, piece_index, offset, data):
        Timing().start_timing("done_blocks")
        piece = self._pieces[piece_index]
        Logger().write(LogVerbosity.All, str(peer.id) + ' Received piece message: ' + str(piece.index) + ', block offset: ' + str(offset))

        if self.torrent.state == TorrentState.Done:
            Logger().write(LogVerbosity.All, 'Received a block but torrent already done')
            self.torrent.overhead += len(data)
            return

        if piece.index < self.torrent.stream_position:
            Logger().write(LogVerbosity.All, 'Received a block which is no longer needed')
            self.torrent.overhead += len(data)
            return

        if piece.done or piece.cleared:
            Logger().write(LogVerbosity.All, 'Received block but piece was already done or cleared')
            self.torrent.overhead += len(data)
            return

        block = piece.get_block_by_offset(offset)
        if block.done:
            Logger().write(LogVerbosity.All, 'Received block but block was already done')
            self.torrent.overhead += len(data)
            return

        self.write_block(piece, block, data)

        self.torrent.left -= block.length
        Stats().add('total_downloaded', block.length)

        if self.init_done:
            if self.torrent.state != TorrentState.Done:
                if self.torrent.left == 0:
                    self.torrent.torrent_done()

        Timing().stop_timing("done_blocks")

    def get_block_by_offset(self, piece_index, offset_in_piece):
        return self.get_piece_by_index(piece_index).get_block_by_offset(offset_in_piece)

    def get_piece_by_offset(self, offset):
        return [x for x in self._pieces.values() if x.start_byte <= offset <= x.end_byte][0]

    def get_all_pieces_in_range(self, start_byte, end_byte):
        return [x for x in self._pieces.values() if x.start_byte < end_byte and x.end_byte > start_byte]

    def get_pieces_by_index_range(self, start, end):
        return [x for x in list(self._pieces.values()) if start <= x.index < end]

    def get_piece_by_index(self, index):
        return self._pieces.get(index)

    def get_pieces_after_index(self, index):
        return [x for x in self._pieces.values() if x.index >= index]

    def write_block(self, piece, block, data):
        if piece.done or piece.validated:
            return

        if piece.write_block(block, data):
            if self.validate_piece(piece):
                Logger().write(LogVerbosity.Debug, "Piece " + str(piece.index) + " has valid hash; done")
                piece.validated = True
                self.bitfield.update_piece(piece.index, True)

                self.torrent.cache_manager.write_piece(piece)

                self.torrent.peer_manager.piece_done(piece)
                self.check_stream_file_hash()
            else:
                Logger().write(LogVerbosity.Info, "Piece " + str(piece.index) + " has invalid hash, re-downloading it")
                piece.reset()
                self.torrent.download_manager.redownload_piece(piece)

    def get_interesting_pieces(self):
        return [x.index for x in self._pieces.values() if x.index > self.torrent.stream_position and not x.done]

    def get_data_bytes_for_hash(self, start_byte, length):
        current_read = 0
        result = bytearray()
        while current_read < length:
            current_byte_to_search = start_byte + current_read
            piece_index = int(math.floor(current_byte_to_search / self.piece_length))

            current_piece = self._pieces.get(piece_index)
            if not current_piece:
                return None

            data = current_piece.get_data()
            can_read_from_piece = current_piece.start_byte + current_piece.length - current_byte_to_search
            offset = current_byte_to_search - current_piece.start_byte
            going_to_copy = min(can_read_from_piece, length - current_read)
            result.extend(data[offset:offset + going_to_copy])
            current_read += going_to_copy
        return result

    def check_stream_file_hash(self):
        if self.broadcasted_hash_data or self.torrent.stream_file_hash is not None:
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
            self.torrent.media_file.first_64k = self.torrent.get_data(0, 65536)
            self.torrent.media_file.last_64k = self.torrent.get_data(self.torrent.media_file.length - 65536, 65536)

    def update_hashes(self, hash_string):
        for i in range(len(hash_string) // 20):
            self.hashes.append(hash_string[i * 20: (i + 1) * 20])

    def validate_piece(self, piece):
        expected_hash = self.hashes[piece.index]
        data = piece.get_data()
        if not data:
            return False

        actual_hash = hashlib.sha1(data).digest()
        return expected_hash[0] == actual_hash[0] and expected_hash[8] == actual_hash[8] and expected_hash[19] == actual_hash[19]

    def stream_buffer_position(self, current_stream_position):
        first_unwritten = [x for x in self._pieces.values() if x.index >= current_stream_position and not x.written]
        if len(first_unwritten) == 0:
            return self.last_piece_index
        return first_unwritten[0].index

    def get_bytes_in_buffer(self, current_stream_position):
        all_written = [x for x in self._pieces.values() if x.index >= current_stream_position and x.written]
        return sum([x.length for x in all_written])

    def stop(self):
        super().stop()
        self.bitfield = None
        self._pieces = []
