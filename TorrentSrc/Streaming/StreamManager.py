import math
from threading import Lock

from InterfaceSrc.VLCPlayer import PlayerState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Streaming.StreamListener import StreamListener
from TorrentSrc.Util.Enums import TorrentState, DownloadMode
from TorrentSrc.Util.Util import write_size

from Shared.Util import current_time


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
        self.listener = StreamListener(torrent, 50009)
        self.buffer = None
        self.end_piece = 0
        self.stream_end_buffer_pieces = 0
        self.init = False
        self.start_buffer = 0
        self.last_request = 0
        self.end_buffer_bytes = 0
        self.end_buffer = 0
        self.start_buffer_bytes = 0
        self.seeking = False
        self.seek_start = 0
        self.initial_play = False

        self.max_in_buffer = Settings.get_int("max_bytes_ready_in_buffer")
        self.max_in_buffer_threshold = Settings.get_int("max_bytes_reached_threshold")
        self.stream_tolerance = Settings.get_int("stream_pause_tolerance")

        self.seek_event_id = EventManager.register_event(EventType.ProcessSeeking, self.seek)
        self.player_event_id = EventManager.register_event(EventType.PlayerStateChange, self.player_change)

        self.listener.start_listening()

    def seek(self):
        self.seek_start = current_time()
        self.seeking = True

    def player_change(self, old_state, new_state):
        if new_state == PlayerState.Playing:
            self.initial_play = True

    def update(self):
        if self.torrent.state == TorrentState.DownloadingMetaData:
            return True

        if not self.init:
            self.init = True
            self.end_piece = int(math.floor(self.torrent.media_file.end_byte / self.torrent.piece_length))
            self.end_buffer_bytes = Settings.get_int("stream_end_buffer")
            self.stream_end_buffer_pieces = math.ceil(self.end_buffer_bytes / self.torrent.piece_length)
            self.start_buffer_bytes = Settings.get_int("stream_start_buffer")

            self.start_buffer = math.ceil(self.start_buffer_bytes / self.torrent.piece_length)
            self.end_buffer = math.ceil(self.torrent.media_file.end_byte - self.end_buffer_bytes / self.torrent.piece_length)

            self.buffer = StreamBuffer(self, self.torrent.piece_length)

        if self.consecutive_pieces_total_length >= self.max_in_buffer \
                and self.torrent.left > self.stream_tolerance:
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

        new_index = int(math.floor(start_byte / self.torrent.piece_length))
        old_stream_pos = self.stream_position_piece_index
        byte_jump = abs(start_byte - self.last_request)

        if self.seeking:
            if self.seek_start + 2000 > current_time():
                pass
            else:
                Logger.write(2, "Seeking for byte " + str(start_byte))
                self.stream_position_piece_index = new_index
                self.seeking = False

                self.buffer.last_consecutive_piece_dirty = True
                self.buffer.update_consecutive()

                self.torrent.download_manager.seek(old_stream_pos, self.stream_position_piece_index)
                if self.torrent.state == TorrentState.Done:
                    self.torrent.unpause()
        elif self.initial_play:
            self.stream_position_piece_index = new_index

        if self.stream_position_piece_index != old_stream_pos:
            Logger.write(2, 'Stream position changed: ' + str(old_stream_pos) + ' -> ' + str(self.stream_position_piece_index))
            self.buffer.last_consecutive_piece_dirty = True

        success, data = self.buffer.get_data_for_stream(start_byte, length)
        self.last_request = start_byte
        return data

    def write_piece(self, piece):
        self.buffer.write_piece(piece)

    def stop(self):
        EventManager.deregister_event(self.seek_event_id)
        self.listener.stop()


class StreamBuffer:

    @property
    def bytes_in_buffer(self):
        self.__lock.acquire()
        total = sum(x.length for x in self.data_ready)
        self.__lock.release()
        return total

    def __init__(self, manager, piece_length):
        self.stream_manager = manager
        self.piece_length = piece_length
        self.data_ready = []
        self.__lock = Lock()
        self.last_consecutive_piece = 0
        self.last_consecutive_piece_dirty = True
        self.stream_start_buffer_bytes = math.ceil(Settings.get_int("stream_start_buffer") / piece_length)
        self.end_piece = math.ceil(
            self.stream_manager.torrent.media_file.end_byte / self.stream_manager.torrent.piece_length)
        self.piece_count_end_buffer = math.ceil(
            Settings.get_int("stream_end_buffer") / self.stream_manager.torrent.piece_length)
        self.buffer_end_start_piece = self.end_piece - self.piece_count_end_buffer

    def get_consecutive_bytes_in_buffer(self, start_from):
        self.update_consecutive()
        return max((self.last_consecutive_piece - start_from) * self.piece_length, 0)

    def get_data_for_hash(self, start_byte, length):
        return self.retrieve_data(start_byte, length)

    def get_data_for_stream(self, start_byte, length):
        result = self.retrieve_data(start_byte, length)
        self.clear(self.stream_manager.stream_position_piece_index)

        return True, result

    def retrieve_data(self, start_byte, length):
        current_read = 0
        result = bytearray()
        while current_read < length:
            current_byte_to_search = start_byte + current_read
            piece_index = int(math.floor(current_byte_to_search / self.piece_length))

            self.__lock.acquire()
            pieces = [x for x in self.data_ready if x.index == piece_index]
            if len(pieces) > 0:
                current_piece = pieces[0]
            else:
                current_piece = None
            self.__lock.release()

            if current_piece is None:
                return None

            data = current_piece.get_data()
            can_read_from_piece = current_piece.start_byte + current_piece.length - current_byte_to_search
            offset = current_byte_to_search - current_piece.start_byte
            going_to_copy = min(can_read_from_piece, length - current_read)
            result.extend(data[offset:offset + going_to_copy])
            current_read += going_to_copy
        return result

    def write_piece(self, piece):
        self.__lock.acquire()
        if piece in self.data_ready:
            self.__lock.release()
            return

        Logger.write(1, "Piece " + str(piece.index) + " ready for streaming")
        self.data_ready.append(piece)
        self.__lock.release()
        self.last_consecutive_piece_dirty = True

        self.clear(self.stream_manager.stream_position_piece_index)

    def clear(self, stream_position):
        self.__lock.acquire()
        for item in self.data_ready:
            if item.index < (stream_position - 1) and item.index > self.stream_start_buffer_bytes and item.index < self.buffer_end_start_piece:
                item.clear()
                self.data_ready.remove(item)

        self.__lock.release()

        self.update_consecutive()

    def update_consecutive(self):
        if not self.last_consecutive_piece_dirty:
            return

        self.__lock.acquire()
        self.data_ready.sort(key=lambda x: x.index)

        start = self.stream_manager.stream_position_piece_index

        for item in self.data_ready:
            if item.index <= start:
                continue

            if item.index == start + 1:
                start = item.index
            else:
                break

        self.__lock.release()
        self.last_consecutive_piece_dirty = False
        self.last_consecutive_piece = start
