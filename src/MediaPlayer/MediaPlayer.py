import datetime
import os
import time

from MediaPlayer.TorrentStreaming.Torrent.Torrent import Torrent

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.Subtitles.SubtitleProvider import SubtitleProvider
from MediaPlayer.TorrentStreaming.DHT.Engine import DHTEngine
from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import current_time, Singleton


class MediaManager(metaclass=Singleton):

    def __init__(self):
        self.media_data = MediaData()
        self.torrent_data = TorrentData()

        self.torrent = None
        self.subtitle_provider = SubtitleProvider()

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()

        EventManager.register_event(EventType.NoPeers, self.stop_torrent)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, lambda files: EventManager.throw_event(EventType.ClientRequest, [self.set_media_file, 1000 * 60 * 60 * 24, "SelectMediaFile", [files]]))
        EventManager.register_event(EventType.TorrentMediaFileSet, lambda x: self._start_playing_torrent())

        VLCPlayer().player_state.register_callback(self.player_state_change)
        self.torrent_observer = CustomThread(self.observe_torrent, "Torrent observer")
        self.torrent_observer.start()

    def start_file(self, url, time):
        if Settings.get_bool("slave"):
            url = Settings.get_string("master_ip") + ":50015/file/" + url

        self.stop_play()
        VLCPlayer().play(url, time)
        self.media_data.type = "File"
        self.media_data.title = os.path.basename(url)
        self.media_data.image = None
        self.media_data.updated()

    def start_radio(self, name, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        self.media_data.type = "Radio"
        self.media_data.title = name
        self.media_data.image = None
        self.media_data.updated()

    def start_episode(self, id, season, episode, title, url, image):
        self.stop_play()
        self._start_torrent(url, None)
        self.media_data.type = "Torrent"
        self.media_data.title = title
        self.media_data.image = image
        self.media_data.updated()

    def start_torrent(self, title, url):
        self.stop_play()
        self._start_torrent(url, None)
        self.media_data.type = "Torrent"
        self.media_data.title = title
        self.media_data.image = None
        self.media_data.updated()

    def start_movie(self, id, title, url, image):
        self.stop_play()
        self._start_torrent(url, None)
        self.media_data.type = "Torrent"
        self.media_data.title = title
        self.media_data.image = image
        self.media_data.updated()

    def start_url(self, title, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        self.media_data.type = "Url"
        self.media_data.title = title
        self.media_data.image = None
        self.media_data.updated()

    def pause_resume(self):
        VLCPlayer().pause_resume()

    def stop_play(self):
        VLCPlayer().stop()
        self.stop_torrent()
        self.media_data.type = None
        self.media_data.title = None
        self.media_data.updated()

    def set_media_file(self, file):
        if not file:
            self.stop_play()
        else:
            self.torrent.set_media_file(file)

    def _start_playing_torrent(self):
        VLCPlayer().play("http://localhost:50009/torrent")

    def _start_torrent(self, url, media_file):
        if self.torrent is not None:
            Logger.write(2, "Can't start new torrent, still torrent active")
            return

        success, torrent = Torrent.create_torrent(1, url)
        if success:
            self.torrent = torrent
            if media_file is not None:
                self.torrent.set_selected_media_file(media_file)
            torrent.start()
            self.last_torrent_start = current_time()
        else:
            Logger.write(2, "Invalid torrent")
            EventManager.throw_event(EventType.Error, ["torrent_error", "Invalid torrent"])
            if self.torrent is not None:
                self.torrent.stop()
                self.torrent = None

            time.sleep(1)

    def player_state_change(self, newState):
        if newState.state == PlayerState.Ended:
            if self.torrent is not None:
                self.torrent.stop()
                Logger.write(2, "Ended " + self.torrent.media_file.name)
                self.torrent = None

        if newState.state == PlayerState.Nothing:
            self.media_data.type = None
            self.media_data.title = None
            self.media_data.updated()

    def stop_torrent(self):
        if self.torrent:
            self.torrent.stop()
            self.torrent = None

    def observe_torrent(self):
        while True:
            if self.torrent is None:
                time.sleep(0.5)
                continue

            self.torrent_data.size = self.torrent.total_size
            self.torrent_data.downloaded = self.torrent.download_counter.total
            self.torrent_data.left = self.torrent.left
            self.torrent_data.overhead = self.torrent.overhead
            self.torrent_data.download_speed = self.torrent.download_counter.value

            self.torrent_data.buffer_position = self.torrent.stream_buffer_position
            self.torrent_data.buffer_total = self.torrent.bytes_total_in_buffer
            self.torrent_data.buffer_size = self.torrent.bytes_ready_in_buffer
            self.torrent_data.stream_position = self.torrent.stream_position
            self.torrent_data.total_streamed = self.torrent.bytes_streamed

            self.torrent_data.state = self.torrent.state

            self.torrent_data.potential = len(self.torrent.peer_manager.potential_peers)
            self.torrent_data.connecting = len(self.torrent.peer_manager.connecting_peers)
            self.torrent_data.connected = len(self.torrent.peer_manager.connected_peers)
            self.torrent_data.disconnected = len(self.torrent.peer_manager.disconnected_peers)
            self.torrent_data.cant_connect = len(self.torrent.peer_manager.cant_connect_peers)

            self.torrent_data.updated()
            time.sleep(0.5)


class TorrentData(Observable):

    def __init__(self):
        super().__init__("TorrentData", 0.5)
        self.size = 0
        self.downloaded = 0
        self.left = 0
        self.overhead = 0
        self.download_speed = 0

        self.buffer_position = 0
        self.buffer_total = 0
        self.buffer_size = 0
        self.stream_position = 0
        self.total_streamed = 0

        self.state = 0

        self.potential = 0
        self.connecting = 0
        self.connected = 0
        self.disconnected = 0
        self.cant_connect = 0


class MediaData(Observable):

    def __init__(self):
        super().__init__("MediaData", 0.5)
        self.type = None
        self.title = None
        self.image = None
