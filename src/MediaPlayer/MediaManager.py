import json
import os
import time
import urllib.parse

import gc

import objgraph

from Controllers.TVManager import TVManager
from MediaPlayer.NextEpisodeManager import NextEpisodeManager
from MediaPlayer.Torrents.Torrent.Torrent import Torrent

from Database.Database import Database, History
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.Subtitles.SubtitleProvider import SubtitleProvider
from MediaPlayer.Torrents.DHT.Engine import DHTEngine
from MediaPlayer.Util.Enums import TorrentState
from MediaPlayer.Util.Util import get_file_info
from Shared.Events import EventType, EventManager
from Shared.Logger import Logger, LogVerbosity
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import current_time, Singleton
from Webserver.APIController import APIController
from Webserver.Controllers.Websocket2.SlaveClientController import SlaveClientController


class MediaManager(metaclass=Singleton):

    def __init__(self):
        self.media_data = MediaData()
        self.torrent_data = TorrentData()

        self.torrent = None
        self.subtitle_provider = SubtitleProvider()
        self.next_episode_manager = NextEpisodeManager()
        self.play_position = 0
        self.play_length = 0

        self.history_id = 0
        self.last_tracking_update = 0

        self.dht_enabled = Settings.get_bool("dht")
        if self.dht_enabled:
            self.dht = DHTEngine()
            self.dht.start()

        EventManager.register_event(EventType.NoPeers, self.stop_torrent)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, self.media_selection_required)
        EventManager.register_event(EventType.TorrentMediaFileSet, lambda x: self._start_playing_torrent())
        EventManager.register_event(EventType.TorrentStopped, lambda: self.on_torrent_stopped())

        VLCPlayer().player_state.register_callback(self.player_state_change)
        self.torrent_observer = CustomThread(self.observe_torrent, "Torrent observer")
        self.torrent_observer.start()
        self.next_epi_thread = None

    def start_file(self, url, time):
        actual_url = url
        if Settings.get_bool("slave"):
            actual_url = "http://" + Settings.get_string("master_ip") + ":50015/file/" + urllib.parse.quote(url)

        self.stop_play()
        VLCPlayer().play(actual_url, time)
        if Settings.get_bool("slave"):
            self.history_id, = SlaveClientController.request_master("add_watched_file", 5, url, current_time())
        else:
            self.history_id = Database().add_watched_file(url, current_time())
        self.media_data.start_update()
        self.media_data.type = "File"
        self.media_data.title = os.path.basename(url)
        self.media_data.url = url
        self.media_data.image = None
        self.media_data.stop_update()
        TVManager().switch_input_to_pi()

    def start_radio(self, name, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        self.media_data.start_update()
        self.media_data.type = "Radio"
        self.media_data.title = name
        self.media_data.image = None
        self.media_data.stop_update()
        TVManager().switch_input_to_pi()

    def start_episode(self, id, season, episode, title, url, image, position):
        self.stop_play()
        self._start_torrent(url, None)
        self.media_data.start_update()
        self.media_data.type = "Show"
        self.media_data.title = title
        self.media_data.image = image
        self.media_data.season = season
        self.media_data.id = id
        self.media_data.episode = episode
        self.media_data.start_from = position
        self.media_data.stop_update()

    def start_torrent(self, title, url, media_file=None):
        self.stop_play()
        self._start_torrent(url, media_file)
        self.media_data.start_update()
        self.media_data.type = "Torrent"
        self.media_data.title = title
        self.media_data.image = None
        self.media_data.stop_update()

    def start_movie(self, id, title, url, image, position):
        self.stop_play()
        self._start_torrent(url, None)
        self.media_data.start_update()
        self.media_data.type = "Movie"
        self.media_data.title = title
        self.media_data.image = image
        self.media_data.id = id
        self.media_data.start_from = position
        self.media_data.stop_update()

    def start_youtube(self, title, url, position):
        self.stop_play()
        VLCPlayer().play(url, position)
        if Settings.get_bool("slave"):
            self.history_id, = SlaveClientController.request_master("add_watched_youtube", 5, title, url, current_time())
        else:
            self.history_id = Database().add_watched_youtube(title, url, current_time())
        self.media_data.start_update()
        self.media_data.type = "YouTube"
        self.media_data.url = url
        self.media_data.title = title
        self.media_data.stop_update()
        TVManager().switch_input_to_pi()

    def start_url(self, title, url):
        self.stop_play()
        VLCPlayer().play(url, 0)
        if Settings.get_bool("slave"):
            self.history_id, = SlaveClientController.request_master("add_watched_url", 5, url, current_time())
        else:
            self.history_id = Database().add_watched_url(url, current_time())
        self.media_data.start_update()
        self.media_data.type = "Url"
        self.media_data.title = title
        self.media_data.stop_update()
        TVManager().switch_input_to_pi()

    def pause_resume(self):
        VLCPlayer().pause_resume()

    def seek(self, position):
        VLCPlayer().set_time(position)

    def change_subtitle(self, track):
        VLCPlayer().set_subtitle_track(track)

    def change_audio(self, track):
        VLCPlayer().set_audio_track(track)

    def change_volume(self, change_volume):
        VLCPlayer().set_volume(change_volume)

    def change_subtitle_delay(self, delay):
        VLCPlayer().set_subtitle_delay(delay)

    def stop_play(self):
        stop_torrent = False
        if VLCPlayer().player_state.state == PlayerState.Nothing:
            stop_torrent = True
        VLCPlayer().stop()
        if stop_torrent:
            self.stop_torrent()

        self.media_data.reset()

    @staticmethod
    def on_torrent_stopped():
        time.sleep(2)
        gc.collect()
        time.sleep(1)

        obj = objgraph.by_type('MediaPlayer.Torrents.Torrent.Torrent.Torrent')
        if len(obj) != 0:
            Logger().write(LogVerbosity.Important, "Torrent not disposed!")
        else:
            Logger().write(LogVerbosity.Info, "Torrent disposed")

    def play_next_episode(self, continue_next):
        if continue_next:
            if self.next_episode_manager.next_type == "File":
                self.start_file(self.next_episode_manager.next_path, 0)
            elif self.next_episode_manager.next_type == "Show":
                self.start_episode(self.next_episode_manager.next_id, self.next_episode_manager.next_season, self.next_episode_manager.next_episode, self.next_episode_manager.next_title, self.next_episode_manager.next_path, self.next_episode_manager.next_img, 0)
            else:
                self.start_torrent(self.next_episode_manager.next_title, self.next_episode_manager.next_path, self.next_episode_manager.next_media_file)

            Logger().write(LogVerbosity.Info, "Playing next: " + self.next_episode_manager.next_title)
        self.next_episode_manager.reset()

    def media_selection_required(self, files):
        if Settings.get_bool("slave"):
            data, = SlaveClientController.request_master("get_history_for_url", 5, self.torrent.uri)
            if data:
                history = [History(x['id'], x['imdb_id'], x['type'], x['title'], x['image'], x['watched_at'], x['season'], x['episode'], x['url'], x['media_file'], x['played_for'], x['length']) for x in json.loads(data)]
            else:
                history = []
        else:
            history = Database().get_history_for_url(self.torrent.uri)

        for file in files:
            seen = [x for x in history if x.media_file == file.path]
            file.seen = len(seen) > 0
            if file.seen:
                seen = seen[-1]
                file.played_for = seen.played_for
                file.play_length = seen.length

        APIController().ui_request("SelectMediaFile", self.set_media_file, 60 * 30, files)

    def set_media_file(self, file, position):
        if not file:
            self.stop_play()
        else:
            self.media_data.start_from = position
            self.torrent.set_media_file(file)

    def _start_playing_torrent(self):
        if Settings.get_bool("slave"):
            self.history_id, = SlaveClientController.request_master("add_watched_torrent", 5, self.media_data.type, self.media_data.title, self.media_data.id, self.torrent.uri, self.torrent.media_file.path, self.media_data.image, self.media_data.season, self.media_data.episode, current_time())
        else:
            self.history_id = Database().add_watched_torrent(self.media_data.type, self.media_data.title, self.media_data.id, self.torrent.uri, self.torrent.media_file.path, self.media_data.image, self.media_data.season, self.media_data.episode, current_time())
        VLCPlayer().play("http://localhost:50009/torrent", self.media_data.start_from)

    def _start_torrent(self, url, media_file):
        if self.torrent is not None:
            Logger().write(LogVerbosity.Important, "Can't start new torrent, still torrent active")
            return

        success, torrent = Torrent.create_torrent(1, url)
        if success:
            self.torrent = torrent
            if media_file is not None:
                self.torrent.set_selected_media_file(media_file)
            torrent.start()
            self.last_torrent_start = current_time()
            TVManager().switch_input_to_pi()
        else:
            Logger().write(LogVerbosity.Important, "Invalid torrent")
            EventManager.throw_event(EventType.Error, ["torrent_error", "Invalid torrent"])
            self.stop_torrent()

    def player_state_change(self, old_state, new_state):
        if old_state.state != new_state.state:
            Logger().write(LogVerbosity.Info, "Player state changed from " + str(old_state.state) + " to " + str(new_state.state))

        if new_state.state == PlayerState.Playing:
            self.play_position = new_state.playing_for
            self.play_length = new_state.length

        if old_state.state != PlayerState.Paused and old_state.state != new_state.state and new_state.state == PlayerState.Playing:
            self.update_subtitles(new_state)
            self.next_epi_thread = CustomThread(lambda: self.next_episode_manager.check_next_episode(self.media_data, self.torrent), "Check next episode", [])
            self.next_epi_thread.start()

        if old_state.state != new_state.state and new_state.state == PlayerState.Nothing:
            self.history_id = 0
            self.media_data.reset()
            self.stop_torrent()
            if self.play_length != 0 and self.play_position / self.play_length > 0.9:
                self.next_episode_manager.notify_next_episode(self.play_next_episode)
            else:
                self.next_episode_manager.reset()
            self.play_position = 0
            self.play_length = 0

        self.update_tracking(new_state)

    def update_subtitles(self, new_state):
        media_type = self.media_data.type
        if media_type == "File":
            if Settings.get_bool("slave"):
                SlaveClientController.request_master_cb("get_file_info", self.process_file_info_for_subtitles, 5, self.media_data.url)
            else:
                size, first_64k, last_64k = get_file_info(self.media_data.url)
                EventManager.throw_event(EventType.SearchSubtitles, [self.media_data.title, size, VLCPlayer().get_length(), first_64k, last_64k])
        elif media_type == "Show" or media_type == "Movie" or media_type == "Torrent":
            EventManager.throw_event(EventType.SearchSubtitles, [os.path.basename(self.torrent.media_file.name), self.torrent.media_file.length, VLCPlayer().get_length(), self.torrent.media_file.first_64k, self.torrent.media_file.last_64k])

    def process_file_info_for_subtitles(self, size, first_64k, last_64k):
        Logger().write(LogVerbosity.Debug, "Received file info from master, requesting subs")
        EventManager.throw_event(EventType.SearchSubtitles, [self.media_data.title, size, VLCPlayer().get_length(), first_64k.encode('utf8'), last_64k.encode('utf8')])

    def update_tracking(self, state):
            if self.media_data.type == "Radio":
                return

            if self.history_id == 0 or state.state != PlayerState.Playing or current_time() - self.last_tracking_update < 5000:
                return

            if state.playing_for > state.length - (state.length * 0.04) or state.length - state.playing_for < 10000:
                if Settings.get_bool("slave"):
                    SlaveClientController.notify_master("update_watching_item", self.history_id, state.length, state.length, current_time())
                else:
                    Database().update_watching_item(self.history_id, state.length, state.length, current_time())
            else:
                if Settings.get_bool("slave"):
                    SlaveClientController.notify_master("update_watching_item", self.history_id, state.playing_for, state.length, current_time())
                else:
                    Database().update_watching_item(self.history_id, state.playing_for, state.length, current_time())
            self.last_tracking_update = current_time()

    def stop_torrent(self):
        if self.torrent:
            thread = CustomThread(self.torrent.stop, "Torrent stopper")
            thread.start()
            self.torrent = None

    def observe_torrent(self):
        while True:
            if self.torrent is None or self.torrent.state == TorrentState.Stopping:
                self.torrent_data.reset()
                time.sleep(0.5)
                continue

            self.torrent_data.start_update()
            self.torrent_data.title = self.torrent.name
            self.torrent_data.size = self.torrent.total_size
            if self.torrent.media_file is not None:
                self.torrent_data.media_file = self.torrent.media_file.name
                self.torrent_data.size = self.torrent.media_file.length
            self.torrent_data.downloaded = self.torrent.network_manager.average_download_counter.total
            self.torrent_data.left = self.torrent.left
            self.torrent_data.overhead = self.torrent.overhead
            self.torrent_data.download_speed = self.torrent.network_manager.average_download_counter.value

            self.torrent_data.buffer_position = self.torrent.stream_buffer_position
            self.torrent_data.buffer_total = self.torrent.bytes_total_in_buffer
            self.torrent_data.stream_position = self.torrent.stream_position
            self.torrent_data.buffer_size = self.torrent.bytes_ready_in_buffer
            self.torrent_data.total_streamed = self.torrent.bytes_streamed

            self.torrent_data.state = self.torrent.state

            self.torrent_data.potential = len(self.torrent.peer_manager.potential_peers)
            self.torrent_data.connecting = len(self.torrent.peer_manager.connecting_peers)
            self.torrent_data.connected = len(self.torrent.peer_manager.connected_peers)
            self.torrent_data.disconnected = len(self.torrent.peer_manager.disconnected_peers)
            self.torrent_data.cant_connect = len(self.torrent.peer_manager.cant_connect_peers)

            self.torrent_data.stop_update()
            time.sleep(0.5)


class TorrentData(Observable):

    def __init__(self):
        super().__init__("TorrentData", 0.5)
        self.title = None
        self.media_file = None
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
        self.stream_speed = 0

        self.state = 0
        self.throttling = False
        self.max_download_speed = 0

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
        self.url = None
        self.image = None
        self.season = None
        self.episode = None
        self.id = None
        self.start_from = 0