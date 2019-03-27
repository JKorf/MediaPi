import math

import time
from pympler import asizeof

from MediaPlayer.TorrentStreaming.Data import Bitfield, Piece
from MediaPlayer.TorrentStreaming.Torrent.TorrentPieceHashValidator import TorrentPieceHashValidator
from MediaPlayer.Util.Enums import TorrentState
from MediaPlayer.Util.MultiQueue import MultiQueue
from Shared.Events import EventManager, EventType
from Shared.LogObject import LogObject
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Timing import Timing
from Shared.Util import current_time, write_size


class TorrentDataManager(LogObject):

    def __init__(self, torrent):
        super().__init__(torrent, "data")
        self.torrent = torrent
        self._pieces = dict()
        self.init_done = False
        self.total_pieces = 0
        self.piece_length = 0
        self.bitfield = None

        self.persistent_pieces = []
        self.total_cleared = 0

        self.done_queue = MultiQueue("Blocks done queue", self.process_done_blocks)

        self.block_size = Settings.get_int("block_size")

        self.piece_hash_validator = TorrentPieceHashValidator()
        self.piece_hash_validator.on_piece_accept = self.piece_hash_valid
        self.piece_hash_validator.on_piece_reject = self.piece_hash_invalid

        self._event_id_log = EventManager.register_event(EventType.Log, self.log_queue)
        self._event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

        self.blocks_done_length = 0

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(LogVerbosity.Important, "       Size of " + str(key) + ": " + write_size(size))

    def check_pieces_size(self):
        Logger().write(LogVerbosity.Important, "    _pieces size: " + write_size(asizeof.asizeof(self._pieces)))
        not_done_pieces = [piece for piece in self._pieces.values() if not piece.done]
        done_pieces = [piece for piece in self._pieces.values() if piece.done]
        cleared_pieces = [piece for piece in self._pieces.values() if piece.cleared]
        stream_index = [piece for piece in self._pieces.values() if piece.index < self.torrent.stream_position]
        stream_index_50_mb = [piece for piece in self._pieces.values() if piece.index > self.torrent.stream_position + (50000000 // self.piece_length)]
        Logger().write(LogVerbosity.Important, "    pieces not done: " + str(len(not_done_pieces)) + " - " + write_size(asizeof.asizeof(not_done_pieces)))
        Logger().write(LogVerbosity.Important, "    pieces done: " + str(len(done_pieces)) + " - " + write_size(asizeof.asizeof(done_pieces)))
        Logger().write(LogVerbosity.Important, "    pieces cleared: " + str(len(cleared_pieces)) + " - " + write_size(asizeof.asizeof(cleared_pieces)))
        Logger().write(LogVerbosity.Important, "    pieces < stream index: " + str(len(stream_index)) + " - " + write_size(asizeof.asizeof(stream_index)))
        Logger().write(LogVerbosity.Important, "    pieces > stream index + 50mb: " + str(len(stream_index_50_mb)) + " - " + write_size(asizeof.asizeof(stream_index_50_mb)))
        Logger().write(LogVerbosity.Important, "    pieces with initialized blocks: " + str(len([piece for piece in self._pieces.values() if len(piece._blocks) > 0])))
        if self.torrent.output_manager.stream_manager.buffer is not None:
            data_ready = [piece for piece in self.torrent.output_manager.stream_manager.buffer.data_ready]
            Logger().write(LogVerbosity.Important, "    pieces in data_ready: " + str(len(data_ready)) + " - " + write_size(asizeof.asizeof(data_ready)))

    def log_queue(self):
        unfinished = [x for x in self._pieces.values() if not x.done]
        unfinished_next = [x for x in self._pieces.values() if not x.done and x.index >= self.torrent.stream_position]

        Logger().write(LogVerbosity.Important, "-- TorrentDataManager state --")
        first = ""
        first_next = ""
        if unfinished:
            first = str(unfinished[0].index)
        if unfinished_next:
            first_next = str(unfinished_next[0].index)
        Logger().write(LogVerbosity.Important, "     Data status: first unfinished=" + first + ", first unfinished after stream pos: " + first_next + ", total unfinished=" + str(len(unfinished)) + " pieces")

    def unregister(self):
        EventManager.deregister_event(self._event_id_log)
        EventManager.deregister_event(self._event_id_stopped)

    def start(self):
        self.done_queue.start()

    def stop(self):
        self.done_queue.stop()

    def set_piece_info(self, piece_length, piece_hashes):
        self.piece_hash_validator.update_hashes(piece_hashes)
        self.piece_length = piece_length
        self.total_pieces = int(math.ceil(self.torrent.total_size / piece_length))
        self.bitfield = Bitfield(self.total_pieces)
        self.init_pieces()

    def init_pieces(self):
        blocks_per_piece = int(math.ceil(self.piece_length / self.block_size))

        stream_start_buffer = Settings.get_int("stream_start_buffer")
        stream_end_buffer = Settings.get_int("stream_end_buffer_tolerance")
        start_piece = math.floor(self.torrent.media_file.start_byte / self.piece_length)
        end_piece = math.ceil(self.torrent.media_file.end_byte / self.piece_length)
        current_byte = start_piece * self.piece_length

        start_time = current_time()
        pers_pieces = ""
        for index in range(end_piece - start_piece):
            relative_current_byte = current_byte - start_piece * self.piece_length
            piece_index = start_piece + index
            persistent = relative_current_byte < stream_start_buffer or current_byte + self.piece_length > self.torrent.media_file.end_byte - stream_end_buffer
            if persistent:
                self.persistent_pieces.append(piece_index)
                pers_pieces += str(piece_index) + ", "

            if current_byte + self.piece_length > self.torrent.total_size:
                # last piece, is not full length
                self._pieces[piece_index] = Piece(self, piece_index, piece_index * blocks_per_piece, current_byte, self.torrent.total_size - current_byte, persistent)
            else:
                self._pieces[piece_index] = Piece(self, piece_index, piece_index * blocks_per_piece, current_byte, self.piece_length, persistent)

            current_byte += self.piece_length

        self.init_done = True
        Logger().write(LogVerbosity.Info, "Pieces initialized, " + str(len(self._pieces)) + " pieces created in " + str(current_time() - start_time) + "ms")
        Logger().write(LogVerbosity.Debug, "Persistent pieces: " + pers_pieces)

    def clear_pieces(self, from_index, to_index):
        cleared = 0
        cleared_size = 0
        for index in range(from_index, to_index):
            piece = self._pieces[index]
            if not piece.cleared and not piece.persistent:
                piece.clear()
                self.total_cleared += piece.length

        Logger().write(LogVerbosity.Debug, "Cleared " + str(cleared) + " piece(s): " + str(write_size(cleared_size)) + ". Total cleared: " + str(write_size(self.total_cleared)))

    def process_done_blocks(self, done_items):
        Timing().start_timing("done_blocks")
        self.blocks_done_length = len(self.done_queue.queue)
        for peer, piece_index, offset, data, timestamp in done_items:
            piece = self._pieces[piece_index]
            Logger().write(LogVerbosity.All, str(peer.id) + ' Received piece message: ' + str(piece.index) + ', block offset: ' + str(offset))

            peer.download_manager.block_done(piece_index * self.piece_length + offset, timestamp)
            if self.torrent.state == TorrentState.Done:
                Logger().write(LogVerbosity.All, 'Received a block but torrent already done')
                self.torrent.overhead += len(data)
                continue

            if piece.index < self.torrent.stream_position and not piece.persistent:
                Logger().write(LogVerbosity.All, 'Received a block which is no longer needed')
                self.torrent.overhead += len(data)
                continue

            if piece.done:
                Logger().write(LogVerbosity.All, 'Received block but piece was already done')
                self.torrent.overhead += len(data)
                continue

            block = piece.get_block_by_offset(offset)
            if block.done:
                Logger().write(LogVerbosity.All, 'Received block but block was already done')
                self.torrent.overhead += len(data)
                continue

            self.write_block(piece, block, data)

            self.torrent.left -= block.length
            Stats.add('total_downloaded', block.length)

        if self.init_done:
            if self.torrent.state != TorrentState.Done:
                if len([x for x in self._pieces.values() if x.index >= self.torrent.stream_position and not x.done]) == 0:
                    self.torrent.torrent_done()

        Timing().stop_timing("done_blocks")

    def piece_hash_valid(self, piece):
        Logger().write(LogVerbosity.All, "Piece " + str(piece.index) + " has valid hash")
        piece.validated = True
        self.torrent.output_manager.add_piece_to_output(piece)

    def piece_hash_invalid(self, piece):
        if not piece.done:
            return

        Logger().write(LogVerbosity.Info, "Piece " + str(piece.index) + " has invalid hash, re-downloading it")
        piece.reset()
        self.torrent.download_manager.redownload_piece(piece)

    def get_block_by_offset(self, piece_index, offset_in_piece):
        return self.get_piece_by_index(piece_index).get_block_by_offset(offset_in_piece)

    def get_piece_by_offset(self, offset):
        return [x for x in self._pieces.values() if x.start_byte <= offset <= x.end_byte][0]

    def get_pieces_by_index_range(self, start, end):
        return [x for x in list(self._pieces.values()) if start <= x.index < end]

    def get_piece_by_index(self, index):
        return self._pieces.get(index)

    def block_done(self, peer, piece_index, offset, data, timestamp):
        self.done_queue.add_item((peer, piece_index, offset, data, timestamp))
        self.blocks_done_length = len(self.done_queue.queue)

    def write_block(self, piece, block, data):
        if piece.done or piece.validated:
            return

        if piece.write_block(block, data):
            self.piece_hash_validator.add_piece_to_hash(piece)

    def is_interested_in(self, bitfield):
        if self.bitfield is None or bitfield is None:
            return False
        return self.bitfield.interested_in(bitfield)

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
