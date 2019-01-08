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
from Shared.Util import current_time, Singleton


class MediaManager(metaclass=Singleton):

    def __init__(self):
        self.mediaData = MediaData()
        self.torrent = None
        self.subtitle_provider = SubtitleProvider()

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()

        # EventManager.register_event(EventType.StartTorrent, self.start_torrent)
        # EventManager.register_event(EventType.StopTorrent, self.stop_torrent)
        EventManager.register_event(EventType.NoPeers, self.stop_torrent)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, lambda files: EventManager.throw_event(EventType.ClientRequest, [self.set_media_file, 1000 * 60 * 60 * 24, "SelectMediaFile", [files]]))

        VLCPlayer().playerState.register_callback(self.player_state_change)

    def set_media_file(self, file):
        if not file:
            self.stop_play()
        else:
            self.torrent.set_media_file(file)
            self._start_playing_torrent()

    def start_file(self, url, time):
        if Settings.get_bool("slave"):
            url = Settings.get_string("master_ip") + ":50015/file/" + url

        self.stop_play()
        VLCPlayer().play(url, time)
        self.mediaData.type = "File"
        self.mediaData.title = os.path.basename(url)
        self.mediaData.updated()

    def start_radio(self, name, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        self.mediaData.type = "Radio"
        self.mediaData.title = name
        self.mediaData.updated()

    def start_episode(self, id, season, episode, title, url, image):
        self.stop_play()
        self._start_torrent(url, None)
        self.mediaData.type = "Torrent"
        self.mediaData.title = title
        self.mediaData.updated()

    def start_torrent(self, title, url):
        self.stop_play()
        self._start_torrent(url, None)
        self.mediaData.type = "Torrent"
        self.mediaData.title = title
        self.mediaData.updated()

    def start_movie(self, id, title, url, image):
        self.stop_play()
        self._start_torrent(url, None)
        self.mediaData.type = "Torrent"
        self.mediaData.title = title
        self.mediaData.updated()

    def start_url(self, title, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        self.mediaData.type = "Url"
        self.mediaData.title = title
        self.mediaData.updated()

    def pause_resume(self):
        VLCPlayer().pause_resume()

    def stop_play(self):
        VLCPlayer().stop()
        self.stop_torrent()
        self.mediaData.type = None
        self.mediaData.title = None
        self.mediaData.updated()

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
            self.mediaData.type = None
            self.mediaData.title = None
            self.mediaData.updated()

    def stop_torrent(self):
        if self.torrent:
            self.torrent.stop()
            self.torrent = None


class MediaData(Observable):

    def __init__(self):
        super().__init__("MediaData", 0.5)
        self.type = None
        self.title = None
