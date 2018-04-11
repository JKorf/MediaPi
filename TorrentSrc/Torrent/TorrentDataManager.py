import math

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Stats import Stats
from TorrentSrc.Data import Bitfield, Piece
from TorrentSrc.Torrent.TorrentPieceHashValidator import TorrentPieceHashValidator

from TorrentSrc.Util.Enums import TorrentState, OutputMode


class TorrentDataManager:

    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces = []
        self.init_done = False
        self.total_pieces = 0
        self.piece_length = 0
        self.bitfield = None
        self.calculating_stream_file_hash = False
        self.blocks_done = []

        self.block_size = Settings.get_int("block_size")

        self.piece_hash_validator = TorrentPieceHashValidator()
        self.piece_hash_validator.on_piece_accept = self.piece_hash_valid
        self.piece_hash_validator.on_piece_reject = self.piece_hash_invalid

    def set_piece_info(self, piece_length, piece_hashes):
        self.piece_hash_validator.update_hashes(piece_hashes)
        self.piece_length = piece_length
        self.total_pieces = int(math.ceil(self.torrent.total_size / piece_length))
        self.bitfield = Bitfield(self.total_pieces)
        self.init_pieces()

    def init_pieces(self):
        current_byte = 0
        blocks_per_piece = int(math.ceil(self.piece_length / self.block_size))

        stream_start_buffer = Settings.get_int("stream_start_buffer")
        stream_end_buffer = Settings.get_int("stream_initial_end_buffer")

        for index in range(self.total_pieces):
            if self.torrent.output_mode == OutputMode.Stream:
                persistent = current_byte < stream_start_buffer or current_byte > self.torrent.media_file.end_byte - stream_end_buffer
            else:
                persistent = False

            if current_byte + self.piece_length > self.torrent.total_size:
                # last piece, is not full length
                self.pieces.append(Piece(index, index * blocks_per_piece, current_byte, self.torrent.total_size - current_byte, persistent))
            else:
                self.pieces.append(Piece(index, index * blocks_per_piece, current_byte, self.piece_length, persistent))

            current_byte += self.piece_length

        self.init_done = True

    def update_write_blocks(self):
        for piece_index, offset, data in list(self.blocks_done):
            block = self.get_block_by_offset(piece_index, offset)
            Logger.write(1, 'Received piece message: ' + str(block.piece_index) + ', block: ' + str(block.index))

            if self.torrent.state == TorrentState.Done:
                Logger.write(1, 'Received a block but were already done')
                self.blocks_done.remove((piece_index, offset, data))
                continue

            if block.piece_index < self.torrent.stream_position:
                Logger.write(1, 'Received a block which is no longer needed')
                self.blocks_done.remove((piece_index, offset, data))
                continue

            if block.done:
                Logger.write(1, 'Received block but piece was already done')
                self.blocks_done.remove((piece_index, offset, data))
                continue

            self.write_block(block, data)
            self.torrent.left -= block.length
            self.torrent.download_counter.add_value(block.length)
            Stats['total_downloaded'].add(block.length)

            self.blocks_done.remove((piece_index, offset, data))

        if self.init_done:
            if self.torrent.state != TorrentState.Done:
                if len([x for x in self.pieces if x.index >= self.torrent.stream_buffer_position and not x.done]) == 0:
                    self.torrent.torrent_done()

        return True

    def piece_hash_valid(self, piece):
        Logger.write(1, "Piece " + str(piece.index) + " has valid hash")
        self.torrent.output_manager.add_piece_to_output(piece)

    def piece_hash_invalid(self, piece):
        Logger.write(2, "Piece " + str(piece.index) + " has invalid hash, re-downloading it")
        piece.reset()
        self.torrent.download_manager.redownload_piece(piece)

    def get_block_by_offset(self, piece_index, offset_in_piece):
        return self.pieces[piece_index].get_block_by_offset(offset_in_piece)

    def get_piece_by_offset(self, offset):
        return [x for x in self.pieces if x.start_byte <= offset and x.end_byte >= offset][0]

    def get_pieces_by_range(self, start, end):
        return [x for x in self.pieces if x.start_byte > start - self.piece_length and x.end_byte <= end + self.piece_length]

    def block_done(self, piece_index, offset, data):
        self.blocks_done.append((piece_index, offset, data))

    def write_block(self, block, data):
        piece = self.pieces[block.piece_index]
        piece.write_block(block, data)
        if piece.done:
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

            ps = [x for x in self.pieces if x.index == piece_index]
            if len(ps) > 0:
                current_piece = ps[0]
            else:
                current_piece = None

            if current_piece is None:
                return None

            data = current_piece.get_data()
            can_read_from_piece = current_piece.start_byte + current_piece.length - current_byte_to_search
            offset = current_byte_to_search - current_piece.start_byte
            going_to_copy = min(can_read_from_piece, length - current_read)
            result.extend(data[offset:offset + going_to_copy])
            current_read += going_to_copy
        return result