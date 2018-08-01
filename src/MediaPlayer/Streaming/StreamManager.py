import math
from threading import Lock

from Interface.TV.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from MediaPlayer.Streaming.StreamListener import StreamListener
from MediaPlayer.Util.Enums import TorrentState, DownloadMode, StreamFileState

from Shared.Util import current_time, write_size


class StreamManager:

    @property
    def bytes_in_buffer(self):
        if self.buffer is None:
            return 0
        return self.buffer.bytes_in_buffer

    @property
    def consecutive_pieces_last_index(self):
        if self.buffer is None:
            return 0
        return self.buffer.last_consecutive_piece

    @property
    def consecutive_pieces_total_length(self):
        if self.buffer is None:
            return 0
        return self.buffer.get_consecutive_bytes_in_buffer(self.stream_position_piece_index)

    def __init__(self, torrent):
        self.torrent = torrent
        self.stream_position_piece_index = 0
        self.listener = StreamListener("TorrentServer", 50009, torrent)
        self.buffer = None
        self.end_piece = 0
        self.piece_count_end_buffer_tolerance = 0
        self.init = False
        self.start_buffer = 0
        self.seek_lock = Lock()

        self.end_buffer_start_byte = 0
        self.start_buffer_end_byte = 0
        self.playing = False
        self.last_request_end = 0

        self.max_in_buffer = Settings.get_int("max_bytes_ready_in_buffer")
        self.max_in_buffer_threshold = Settings.get_int("max_bytes_reached_threshold")
        self.stream_tolerance = Settings.get_int("stream_pause_tolerance")

        self.player_state_id = EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)
        self.listener.start_listening()

    def player_state_change(self, old, new):
        if new == PlayerState.Playing:
            self.playing = True
        else:
            self.playing = False

    def update(self):
        if self.torrent.is_preparing:
            return True

        if not self.init:
            self.init = True
            self.end_buffer_start_byte = self.torrent.media_file.length - Settings.get_int("stream_end_buffer_tolerance")
            self.start_buffer_end_byte = Settings.get_int("stream_start_buffer")

            self.end_piece = int(math.floor(self.torrent.media_file.end_byte / self.torrent.piece_length))
            self.piece_count_end_buffer_tolerance = math.ceil(
                Settings.get_int("stream_end_buffer_tolerance") / self.torrent.piece_length)
            self.buffer = StreamBuffer(self, self.torrent.piece_length)
            self.change_stream_position(self.torrent.media_file.start_byte)

        if self.consecutive_pieces_total_length >= self.max_in_buffer and self.torrent.left > self.stream_tolerance:
            if self.torrent.state == TorrentState.Downloading:
                Logger.write(2, "Pausing torrent: left to download = " + write_size((self.end_piece - self.consecutive_pieces_last_index) * self.torrent.piece_length))
                self.torrent.pause()
        elif self.torrent.state == TorrentState.Paused:
            if self.consecutive_pieces_total_length < self.max_in_buffer - self.max_in_buffer_threshold:
                self.torrent.unpause()

        if self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer > 50000000 and self.torrent.download_manager.download_mode == DownloadMode.Full:
            Logger.write(2, "Entering ImportantOnly download mode: " + write_size(self.torrent.bytes_total_in_buffer) + " in buffer total, " + write_size(self.consecutive_pieces_total_length) + " consequtive")
            self.torrent.download_manager.download_mode = DownloadMode.ImportantOnly
        elif self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer < 30000000 and self.torrent.download_manager.download_mode == DownloadMode.ImportantOnly:
            Logger.write(2, "Leaving ImportantOnly download mode")
            self.torrent.download_manager.download_mode = DownloadMode.Full

        return True

    def get_data_bytes_for_hash(self, start_byte, length):
        return self.buffer.get_data_for_hash(start_byte, length)

    def get_data_for_stream(self, start_byte, length):
        if not self.init:
            return None

        relative_start_byte = start_byte - self.torrent.media_file.start_byte

        # if new request and we are seeking (media_file.state == Seeking) check if it is in the start or end buffer.
        # If it is in either we shouldn't change stream position. once we start playing again we should update the
        # stream position to where we are then
        with self.seek_lock:

            if self.torrent.media_file.state == StreamFileState.Playing:
                if start_byte + length != self.last_request_end\
                        and self.last_request_end != 0\
                        and (relative_start_byte > self.start_buffer_end_byte and relative_start_byte + length < self.end_buffer_start_byte)\
                        and start_byte - self.last_request_end != 0:
                        Logger.write(2, "Last: " + str(self.last_request_end) + ", this: " + str(start_byte))
                        # not a follow up request.. Probably seeking
                        self.seek(start_byte)
                else:
                    # normal flow, we are playing and should update the stream position
                    self.change_stream_position(start_byte)

            elif self.torrent.media_file.state == StreamFileState.MetaData:
                # Requests to search for metadata. Normally the first x bytes and last x bytes of the file. Don't change
                if self.torrent.piece_length:
                    request_piece = int(math.floor(start_byte / self.torrent.piece_length))
                    if relative_start_byte > self.start_buffer_end_byte and relative_start_byte + length < self.end_buffer_start_byte:
                        if request_piece not in self.torrent.download_manager.upped_prios:
                            Logger.write(2, "Received request for metadata not in buffer. Upping prio for " + str(request_piece))
                            # not a piece currently marked as buffer, should update priority
                            self.torrent.download_manager.up_priority(request_piece)

            elif self.torrent.media_file.state == StreamFileState.Seeking:
                # Seeking to a new position. Some metadata requests are expected. Only change if not in start/end buffer
                if relative_start_byte < self.start_buffer_end_byte or relative_start_byte + length > self.end_buffer_start_byte:
                    if self.playing:
                        # If request is for start/end buffer but we are playing do a seek
                        self.seek(start_byte)
                else:
                    self.seek(start_byte)

            self.last_request_end = start_byte + length

            data = self.buffer.get_data_for_stream(start_byte, length)
        return data

    def seek(self, start_byte):
        old_stream_position = self.stream_position_piece_index
        self.change_stream_position(start_byte)
        self.torrent.download_manager.seek(old_stream_position, self.stream_position_piece_index)
        self.torrent.media_file.set_state(StreamFileState.Playing)
        self.buffer.seek(self.stream_position_piece_index)

    def change_stream_position(self, start_byte):
        new_index = int(math.floor(start_byte / self.torrent.piece_length))
        if new_index != self.stream_position_piece_index:
            Logger.write(2, 'Stream position changed: ' + str(self.stream_position_piece_index) + ' -> ' + str(
                new_index))
            self.stream_position_piece_index = new_index
            self.buffer.last_consecutive_piece_dirty = True

    def write_piece(self, piece):
        self.buffer.write_piece(piece)

    def stop(self):
        EventManager.deregister_event(self.player_state_id)
        self.listener.stop()


class StreamBuffer:

    @property
    def bytes_in_buffer(self):
        with self.__lock:
            total = sum(x.length for x in self.data_ready)
        return total

    def __init__(self, manager, piece_length):
        self.stream_manager = manager
        self.piece_length = piece_length
        self.data_ready = []
        self.__lock = Lock()
        self.last_consecutive_piece = 0
        self.last_consecutive_piece_dirty = True
        self.end_piece = math.ceil(
            self.stream_manager.torrent.media_file.end_byte / self.stream_manager.torrent.piece_length)

    def seek(self, new_index):
        self.data_ready = [x for x in self.data_ready
                           if x.persistent or
                           (x.index >= new_index
                           and (x.index - new_index) * self.piece_length < 100000000)]

    def get_consecutive_bytes_in_buffer(self, start_from):
        self.update_consecutive()
        return max((self.last_consecutive_piece - start_from) * self.piece_length, 0)

    def get_data_for_hash(self, start_byte, length):
        return self.retrieve_data(start_byte, length)

    def get_data_for_stream(self, start_byte, length):
        result = self.retrieve_data(start_byte, length)
        self.clear(self.stream_manager.stream_position_piece_index)
        return result

    def retrieve_data(self, start_byte, length):
        current_read = 0
        result = bytearray()
        while current_read < length:
            current_byte_to_search = start_byte + current_read
            piece_index = int(math.floor(current_byte_to_search / self.piece_length))

            current_piece = None
            with self.__lock:
                pieces = [x for x in self.data_ready if x.index == piece_index]
                if len(pieces) > 0:
                    current_piece = pieces[0]

            if current_piece is None:
                return None

            data = current_piece.get_data()
            if data is None:
                return None

            can_read_from_piece = current_piece.start_byte + current_piece.length - current_byte_to_search
            offset = current_byte_to_search - current_piece.start_byte
            going_to_copy = min(can_read_from_piece, length - current_read)
            result.extend(data[offset:offset + going_to_copy])
            current_read += going_to_copy
        return result

    def write_piece(self, piece):
        with self.__lock:
            if piece in self.data_ready:
                return

            Logger.write(1, "Piece " + str(piece.index) + " ready for streaming")
            self.data_ready.append(piece)

        self.last_consecutive_piece_dirty = True
        self.clear(self.stream_manager.stream_position_piece_index)

    def clear(self, stream_position):
        with self.__lock:
            for piece in self.data_ready:
                if piece.index < (stream_position - 1) and not piece.persistent:
                    piece.clear()
                    self.data_ready.remove(piece)

        self.update_consecutive()

    def update_consecutive(self):
        if not self.last_consecutive_piece_dirty:
            return

        with self.__lock:
            self.data_ready.sort(key=lambda x: x.index)

            start = self.stream_manager.stream_position_piece_index

            for item in self.data_ready:
                if item.index <= start:
                    continue

                if item.index == start + 1:
                    start = item.index
                else:
                    break

        self.last_consecutive_piece_dirty = False
        self.last_consecutive_piece = start
