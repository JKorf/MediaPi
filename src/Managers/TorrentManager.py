import datetime
import time

from Database.Database import Database
from Interface.TV.VLCPlayer import PlayerState
from MediaPlayer.DHT2.Engine import DHTEngine
from MediaPlayer.Subtitles.SubtitleProvider import SubtitleProvider
from MediaPlayer.Torrent.Torrent import Torrent
from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time, Singleton


class TorrentManager(metaclass=Singleton):

    def __init__(self):
        self.torrent = None
        self.subtitle_provider = SubtitleProvider()
        self.last_torrent_start = 0

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()

        EventManager.register_event(EventType.StartTorrent, self.start_torrent)
        EventManager.register_event(EventType.TorrentMediaFileSet, self.media_file_set)
        EventManager.register_event(EventType.StopTorrent, self.stop_torrent)
        EventManager.register_event(EventType.PlayerStateChange, self.player_state_change)
        EventManager.register_event(EventType.NoPeers, self.stop_torrent)

    def start_torrent(self, url, media_file):
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

    def media_file_set(self):
        if Database().last_history_add < self.last_torrent_start - 100:
            Database().add_watched_torrent_file(self.torrent.name, self.torrent.uri, self.torrent.media_file.path, datetime.datetime.now().isoformat())

    def player_state_change(self, old_state, new_state):
        if new_state == PlayerState.Ended:
            if self.torrent is not None:
                self.torrent.stop()
                Logger.write(2, "Ended " + self.torrent.media_file.name)
                self.torrent = None

    def stop_torrent(self):
        if self.torrent:
            self.torrent.stop()
            self.torrent = None
