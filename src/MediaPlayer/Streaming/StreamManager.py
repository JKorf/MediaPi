import math
from threading import Lock

from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.Streaming.StreamListener import StreamListener
from MediaPlayer.Util.Enums import TorrentState, DownloadMode
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import write_size


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
        self.has_played = False
        self.last_request_end = 0

        self.max_in_buffer = Settings.get_int("max_bytes_ready_in_buffer")
        self.max_in_buffer_threshold = Settings.get_int("max_bytes_reached_threshold")
        self.stream_tolerance = Settings.get_int("stream_pause_tolerance")

        VLCPlayer().player_state.register_callback(self.player_change)
        self.listener.start_listening()

    def player_change(self, new):
        if new.state == PlayerState.Playing:
            self.has_played = True

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

        if self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer > 40000000 and self.torrent.download_manager.download_mode == DownloadMode.Full:
            Logger.write(2, "Entering ImportantOnly download mode: " + write_size(self.torrent.bytes_total_in_buffer) + " in buffer total, " + write_size(self.consecutive_pieces_total_length) + " consequtive")
            self.torrent.download_manager.download_mode = DownloadMode.ImportantOnly
        elif self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer < 20000000 and self.torrent.download_manager.download_mode == DownloadMode.ImportantOnly:
            Logger.write(2, "Leaving ImportantOnly download mode")
            self.torrent.download_manager.download_mode = DownloadMode.Full

        return self.buffer.update()

    def get_data_bytes_for_hash(self, start_byte, length):
        return self.buffer.get_data_for_hash(start_byte, length)

    def get_data_for_stream(self, start_byte, length):
        if not self.init:
            return None

        relative_start_byte = start_byte - self.torrent.media_file.start_byte

        with self.seek_lock:
            if self.last_request_end == start_byte + length:
                # If same request as last time, just try to retrieve data
                return self.buffer.get_data_for_stream(start_byte, length)

            if start_byte == self.last_request_end:
                # If follow up request of last, change pos and retrieve data
                self.last_request_end = start_byte + length
                if self.has_played:
                    self.change_stream_position(start_byte)
                return self.buffer.get_data_for_stream(start_byte, length)

            if relative_start_byte < self.start_buffer_end_byte or relative_start_byte > self.end_buffer_start_byte:
                # If not follow up and in metadata range, just return data
                self.last_request_end = start_byte + length
                return self.buffer.get_data_for_stream(start_byte, length)

            # This request is not the same as last, not following up, and not in metadata range
            # Seeking?
            request_piece = int(math.floor(start_byte / self.torrent.piece_length))
            self.last_request_end = start_byte + length
            if request_piece not in self.torrent.download_manager.upped_prios:
                Logger.write(2, "Received stray request, going to search to " + str(request_piece))
                self.seek(start_byte)
                self.last_request_end = start_byte + length
                return self.buffer.get_data_for_stream(start_byte, length)

    def seek(self, start_byte):
        old_stream_position = self.stream_position_piece_index
        self.change_stream_position(start_byte)
        index_change = int(math.floor(start_byte / self.torrent.piece_length)) - old_stream_position
        if 0 <= index_change < 2:  # If it's the same piece or only one piece forwards dont seek
            return
        self.torrent.download_manager.seek(old_stream_position, self.stream_position_piece_index)
        self.buffer.seek(self.stream_position_piece_index)

    def change_stream_position(self, start_byte):
        new_index = int(math.floor(start_byte / self.torrent.piece_length))
        if new_index != self.stream_position_piece_index:
            Logger.write(2, 'Stream position changed: ' + str(self.stream_position_piece_index) + ' -> ' + str(
                new_index))
            self.stream_position_piece_index = new_index

    def write_pieces(self, pieces):
        self.buffer.write_pieces(pieces)

    def stop(self):
        self.torrent = None
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
        self.data_ready = set()
        self.__lock = Lock()
        self.last_check_start_piece = 0
        self.last_consecutive_piece = 0

    def update(self):
        with self.__lock:
            self.data_ready = {x for x in self.data_ready if x.index >= self.stream_manager.stream_position_piece_index or x.persistent}

        self.update_consecutive(True)
        return True

    def seek(self, new_index):
        self.data_ready = {x for x in self.data_ready
                           if x.persistent or
                           (x.index >= new_index
                           and (x.index - new_index) * self.piece_length < 100000000)}
        self.update_consecutive(True)

    def get_consecutive_bytes_in_buffer(self, start_from):
        return max((self.last_consecutive_piece - start_from) * self.piece_length, 0)

    def get_data_for_hash(self, start_byte, length):
        return self.retrieve_data(start_byte, length)

    def get_data_for_stream(self, start_byte, length):
        data = self.retrieve_data(start_byte, length)
        self.update_consecutive(False)
        return data

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

    def write_pieces(self, pieces):
        with self.__lock:
            self.data_ready.update(pieces)

        self.update_consecutive(True)

    def update_consecutive(self, force):
        if not force and self.last_check_start_piece == self.stream_manager.stream_position_piece_index:
            return

        with self.__lock:
            ordered_data = sorted(self.data_ready, key=lambda x: x.index)
            start = self.stream_manager.stream_position_piece_index

            for item in ordered_data:
                if item.index <= start:
                    continue

                if item.index == start + 1:
                    start = item.index
                else:
                    break

        self.last_consecutive_piece = start
        self.last_check_start_piece = self.stream_manager.stream_position_piece_index
