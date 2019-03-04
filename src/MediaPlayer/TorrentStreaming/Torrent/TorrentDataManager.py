import math
from threading import Lock

from pympler import asizeof

from MediaPlayer.TorrentStreaming.Data import Bitfield, Piece
from MediaPlayer.TorrentStreaming.Torrent.TorrentPieceHashValidator import TorrentPieceHashValidator
from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Stats import Stats
from Shared.Util import current_time, write_size


class TorrentDataManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self._pieces = dict()
        self.init_done = False
        self.total_pieces = 0
        self.piece_length = 0
        self.bitfield = None
        self.blocks_done = []
        self.persistent_pieces = []
        self.blocks_done_lock = Lock()
        self.total_cleared = 0

        self.block_size = Settings.get_int("block_size")

        self.piece_hash_validator = TorrentPieceHashValidator()
        self.piece_hash_validator.on_piece_accept = self.piece_hash_valid
        self.piece_hash_validator.on_piece_reject = self.piece_hash_invalid

        self.event_id_log = EventManager.register_event(EventType.Log, self.log_queue)
        self.event_id_stopped = EventManager.register_event(EventType.TorrentStopped, self.unregister)

    def check_size(self):
        for key, size in sorted([(key, asizeof.asizeof(value)) for key, value in self.__dict__.items()], key=lambda key_value: key_value[1], reverse=True):
            Logger().write(2, "       Size of " + str(key) + ": " + write_size(size))

    def check_pieces_size(self):
        Logger().write(2, "    _pieces size: " + write_size(asizeof.asizeof(self._pieces)))
        not_done_pieces = [piece for piece in self._pieces.values() if not piece.done]
        done_pieces = [piece for piece in self._pieces.values() if piece.done]
        cleared_pieces = [piece for piece in self._pieces.values() if piece.cleared]
        stream_index = [piece for piece in self._pieces.values() if piece.index < self.torrent.stream_position]
        stream_index_50_mb = [piece for piece in self._pieces.values() if piece.index > self.torrent.stream_position + (50000000 // self.piece_length)]
        Logger().write(2, "    pieces not done: " + str(len(not_done_pieces)) + " - " + write_size(asizeof.asizeof(not_done_pieces)))
        Logger().write(2, "    pieces done: " + str(len(done_pieces)) + " - " + write_size(asizeof.asizeof(done_pieces)))
        Logger().write(2, "    pieces cleared: " + str(len(cleared_pieces)) + " - " + write_size(asizeof.asizeof(cleared_pieces)))
        Logger().write(2, "    pieces < stream index: " + str(len(stream_index)) + " - " + write_size(asizeof.asizeof(stream_index)))
        Logger().write(2, "    pieces > stream index + 50mb: " + str(len(stream_index_50_mb)) + " - " + write_size(asizeof.asizeof(stream_index_50_mb)))
        Logger().write(2, "    pieces with initialized blocks: " + str(len([piece for piece in self._pieces.values() if len(piece._blocks) > 0])))
        if self.torrent.output_manager.stream_manager.buffer is not None:
            data_ready = [piece for piece in self.torrent.output_manager.stream_manager.buffer.data_ready]
            Logger().write(2, "    pieces in data_ready: " + str(len(data_ready)) + " - " + write_size(asizeof.asizeof(data_ready)))

    def log_queue(self):
        unfinished = [x for x in self._pieces.values() if not x.done]
        unfinished_next = [x for x in self._pieces.values() if not x.done and x.index >= self.torrent.stream_position]

        Logger().write(3, "-- TorrentDataManager state --")
        first = ""
        first_next = ""
        if unfinished:
            first = str(unfinished[0].index)
        if unfinished_next:
            first_next = str(unfinished_next[0].index)
        Logger().write(3, "     Data status: first unfinished=" + first + ", first unfinished after stream pos: " + first_next + ", total unfinished=" + str(len(unfinished)) + " pieces")

    def unregister(self):
        EventManager.deregister_event(self.event_id_log)
        EventManager.deregister_event(self.event_id_stopped)

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
                self._pieces[piece_index] = Piece(piece_index, piece_index * blocks_per_piece, current_byte, self.torrent.total_size - current_byte, persistent)
            else:
                self._pieces[piece_index] = Piece(piece_index, piece_index * blocks_per_piece, current_byte, self.piece_length, persistent)

            current_byte += self.piece_length

        self.init_done = True
        Logger().write(2, "Pieces initialized, " + str(len(self._pieces)) + " pieces created in " + str(current_time() - start_time) + "ms")
        Logger().write(2, "Persistent pieces: " + pers_pieces)

    def cleanup_used_pieces(self):
        stream_pos = self.torrent.stream_position
        cleared = 0
        cleared_size = 0
        for piece in [x for x in self._pieces.values() if x.index < stream_pos and not x.cleared and not x.persistent]:
            piece.clear()
            self.total_cleared += piece.length
            cleared += 1
            cleared_size += piece.length
        if cleared > 0:
            Logger().write(2, "Cleared " + str(cleared) + " piece(s): " + str(write_size(cleared_size)) + ". Total cleared: " + str(write_size(self.total_cleared)))
        return True

    def update_write_blocks(self):
        block_count = 0

        with self.blocks_done_lock:
            blocks = list(self.blocks_done)
            self.blocks_done.clear()

        for peer, piece_index, offset, data in blocks:
            block_count += 1

            piece = self._pieces[piece_index]
            Logger().write(1, str(peer.id) + ' Received piece message: ' + str(piece.index) + ', block offset: ' + str(offset))

            peer.download_manager.block_done(piece_index * self.piece_length + offset)
            if self.torrent.state == TorrentState.Done:
                Logger().write(1, 'Received a block but were already done')
                self.torrent.overhead += len(data)
                continue

            if piece.index < self.torrent.stream_position and not piece.persistent:
                Logger().write(1, 'Received a block which is no longer needed')
                self.torrent.overhead += len(data)
                continue

            if piece.done:
                Logger().write(1, 'Received block but piece was already done')
                self.torrent.overhead += len(data)
                continue

            block = piece.get_block_by_offset(offset)
            if block.done:
                Logger().write(1, 'Received block but block was already done')
                self.torrent.overhead += len(data)
                continue

            self.write_block(piece, block, data)

            self.torrent.left -= block.length
            Stats.add('total_downloaded', block.length)

        if self.init_done:
            if self.torrent.state != TorrentState.Done:
                if len([x for x in self._pieces.values() if x.index >= self.torrent.stream_position and not x.done]) == 0:
                    self.torrent.torrent_done()
        return True

    def piece_hash_valid(self, piece):
        Logger().write(1, "Piece " + str(piece.index) + " has valid hash")
        piece.validated = True
        self.torrent.output_manager.add_piece_to_output(piece)

    def piece_hash_invalid(self, piece):
        if not piece.done:
            return

        Logger().write(2, "Piece " + str(piece.index) + " has invalid hash, re-downloading it")
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

    def block_done(self, peer, piece_index, offset, data):
        with self.blocks_done_lock:
            self.blocks_done.append((peer, piece_index, offset, data))

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

    def stop(self):
        self.torrent = None
