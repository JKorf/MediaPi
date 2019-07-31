import math

from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.Torrents.Streaming.StreamListener import StreamListener
from MediaPlayer.Torrents.TorrentManager import TorrentManager
from MediaPlayer.Util.Enums import DownloadMode
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Util import write_size


class StreamManager(TorrentManager):

    def __init__(self, torrent):
        super().__init__(torrent, "stream manager")
        self.torrent = torrent
        self.stream_position_piece_index = 0
        self.listener = StreamListener("TorrentServer", 50009, torrent)
        self.init = False
        self.start_buffer = 0

        self.end_buffer_start_byte = 0
        self.start_buffer_end_byte = 0
        self.has_played = False
        self.last_request_end = 0

        VLCPlayer().player_state.register_callback(self.player_change)
        self.listener.start_listening()

    def player_change(self, old, new):
        if new.state == PlayerState.Playing:
            self.has_played = True

    def init_buffer(self):
        self.init = True
        self.end_buffer_start_byte = self.torrent.media_file.length - Settings.get_int("stream_end_buffer_tolerance")
        self.start_buffer_end_byte = Settings.get_int("stream_start_buffer")
        self.change_stream_position(self.torrent.media_file.start_byte)

    def get_data(self, start_byte, length):
        if not self.init:
            self.init_buffer()

        if self.last_request_end == start_byte + length:
            # If same request as last time, just try to retrieve data
            return self.retrieve_data(start_byte, length)

        if start_byte == self.last_request_end:
            # If follow up request of last, change pos and retrieve data
            self.last_request_end = start_byte + length
            if self.has_played:
                self.change_stream_position(start_byte)
            return self.retrieve_data(start_byte, length)

        if start_byte < self.start_buffer_end_byte or start_byte > self.end_buffer_start_byte:
            # If not follow up and in metadata range, just return data
            self.last_request_end = start_byte + length
            if self.has_played:
                self.seek(start_byte)
            return self.retrieve_data(start_byte, length)

        # This request is not the same as last, not following up, and not in metadata range
        # Seeking?
        request_piece = int(math.floor(start_byte / self.torrent.piece_length))
        self.last_request_end = start_byte + length
        Logger().write(LogVerbosity.Info, "Received stray request, going to search to " + str(request_piece))
        self.seek(start_byte)
        return self.retrieve_data(start_byte, length)

    def retrieve_data(self, start_byte, length):
        pieces = self.torrent.data_manager.get_all_pieces_in_range(start_byte + self.torrent.media_file.start_byte, start_byte + self.torrent.media_file.start_byte + length)
        if not all(x.written for x in pieces):
            return None

        return self.torrent.cache_manager.read_bytes(start_byte, length)

    def seek(self, start_byte):
        old_stream_position = self.stream_position_piece_index
        self.change_stream_position(start_byte)
        index_change = int(math.floor(start_byte / self.torrent.piece_length)) - old_stream_position
        if 0 <= index_change < 2:  # If it's the same piece or only one piece forwards dont seek
            return

        Logger().write(LogVerbosity.Info, "Seeking to byte " + str(start_byte))
        self.torrent.download_manager.seek(old_stream_position, self.stream_position_piece_index)

    def change_stream_position(self, start_byte):
        new_index = int(math.floor(start_byte / self.torrent.piece_length))
        if new_index != self.stream_position_piece_index:
            Logger().write(LogVerbosity.Debug, 'Stream position changed: ' + str(self.stream_position_piece_index) + ' -> ' + str(
                new_index))
            self.stream_position_piece_index = new_index

    def update(self):
        if self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer > Settings.get_int("important_only_start_threshold") and self.torrent.download_manager.download_mode == DownloadMode.Full:
            Logger().write(LogVerbosity.Info, "Entering ImportantOnly download mode: " + write_size(self.torrent.bytes_total_in_buffer) + " in buffer total")
            self.torrent.download_manager.download_mode = DownloadMode.ImportantOnly
        elif self.torrent.bytes_total_in_buffer - self.torrent.bytes_ready_in_buffer < Settings.get_int("important_only_stop_threshold") and self.torrent.download_manager.download_mode == DownloadMode.ImportantOnly:
            Logger().write(LogVerbosity.Info, "Leaving ImportantOnly download mode")
            self.torrent.download_manager.download_mode = DownloadMode.Full

    def stop(self):
        self.listener.stop()
        super().stop()