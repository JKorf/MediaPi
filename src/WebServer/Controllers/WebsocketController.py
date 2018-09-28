from threading import Lock

import time

import psutil

from Interface.TV.VLCPlayer import PlayerState
from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from WebServer.Models import MediaFile, WebSocketMessage, Status, CurrentMedia, MediaInfo


class WebsocketController:

    clients = []
    _ws_lock = Lock()
    program = None
    update_loop_count = 0

    @staticmethod
    def init(program):
        WebsocketController.program = program
        EventManager.register_event(EventType.NextEpisodeSelection, WebsocketController.next_episode_selection)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, WebsocketController.media_selection_required)
        EventManager.register_event(EventType.TorrentMediaFileSelection, WebsocketController.media_selected)
        EventManager.register_event(EventType.PlayerStateChange, WebsocketController.player_state_changed)
        EventManager.register_event(EventType.PlayerError, WebsocketController.player_error)
        EventManager.register_event(EventType.Seek, WebsocketController.player_seeking)
        EventManager.register_event(EventType.SetVolume, WebsocketController.player_volume)
        EventManager.register_event(EventType.SetSubtitleId, WebsocketController.player_subtitle_id)
        EventManager.register_event(EventType.SetSubtitleOffset, WebsocketController.player_subtitle_offset)
        EventManager.register_event(EventType.Error, WebsocketController.application_error)

        update_thread = CustomThread(WebsocketController.update_loop, "socket update loop")
        update_thread.start()

    @staticmethod
    def update_loop():
        while True:
            if WebsocketController.update_loop_count % 3 == 0:
                status_data = WebsocketController.get_status_data()
                WebsocketController.broadcast("update", "status", status_data)

            if WebsocketController.program.gui_manager.player.state != PlayerState.Nothing:
                player_data = WebsocketController.get_player_data()
                WebsocketController.broadcast("update", "player", player_data)

            if WebsocketController.program.torrent_manager.torrent is not None:
                media_data = WebsocketController.get_media_data()
                WebsocketController.broadcast("update", "media", media_data)
                WebsocketController.update_loop_count = -1

            time.sleep(1)
            WebsocketController.update_loop_count += 1
            if WebsocketController.update_loop_count == 1000:
                WebsocketController.update_loop_count = 0

    @staticmethod
    def opening_client(client):
        if client not in WebsocketController.clients:
            Logger.write(2, "New connection")
            WebsocketController.clients.append(client)
            if WebsocketController.program.torrent_manager.torrent and WebsocketController.program.torrent_manager.torrent.state == TorrentState.WaitingUserFileSelection:
                if not Settings.get_bool("slave"):
                    watched_files = [f[9] for f in WebsocketController.program.database.get_watched_torrent_files(WebsocketController.program.torrent_manager.torrent.uri)]
                    files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in [y for y in WebsocketController.program.torrent_manager.torrent.files if y.is_media]]
                else:
                    files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in [y for y in WebsocketController.program.torrent_manager.torrent.files if y.is_media]]

                client.write_message(to_JSON(WebSocketMessage('request', 'media_selection', files)))

    @staticmethod
    def closing_client(client):
        if client in WebsocketController.clients:
            Logger.write(2, "Connection closed")
            WebsocketController.clients.remove(client)

    @staticmethod
    def broadcast(event, method, parameters=None):
        if parameters is None:
            parameters = ""

        with WebsocketController._ws_lock:
            for client in WebsocketController.clients:
                try:
                    client.write_message(to_JSON(WebSocketMessage(event, method, parameters)))
                except:
                    Logger.write(2, "Failed to send msg to client because client is closed")

    @staticmethod
    def next_episode_selection(path, name, season, episode, type, media_file, img):
        WebsocketController.broadcast("request", "next_episode", MediaFile(path, name, 0, season, episode, type, media_file, img, False))

    @staticmethod
    def media_selected(file):
        WebsocketController.broadcast("request", "media_selection_close")

    @staticmethod
    def media_selection_required(files):
        if not Settings.get_bool("slave"):
            watched_files = [f[9] for f in WebsocketController.program.database.get_watched_torrent_files(WebsocketController.program.torrent_manager.torrent.uri)]
            files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in files]
        else:
            files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in files]
        WebsocketController.broadcast("request", "media_selection", files)

    @staticmethod
    def player_state_changed(old_state, state):
        WebsocketController.broadcast("player_event", "state_change", state.value)

    @staticmethod
    def player_error():
        WebsocketController.broadcast("player_event", "error")

    @staticmethod
    def player_seeking(pos):
        WebsocketController.broadcast("player_event", "seek", pos / 1000)

    @staticmethod
    def player_volume(vol):
        WebsocketController.broadcast("player_event", "volume", vol)

    @staticmethod
    def player_subtitle_id(id):
        WebsocketController.broadcast("player_event", "subtitle_id", id)

    @staticmethod
    def player_subs_done_change(done):
        WebsocketController.broadcast("player_event", "subs_done_change", done)

    @staticmethod
    def player_subtitle_offset(offset):
        WebsocketController.broadcast("player_event", "subtitle_offset", float(offset) / 1000 / 1000)

    @staticmethod
    def application_error(error_type, error_message):
        WebsocketController.broadcast("error_event", error_type, error_message)

    @staticmethod
    def get_status_data():
        speed = -1
        ready = -1
        torrent_state = -1
        connected_peers = -1
        potential_peers = -1
        if WebsocketController.program.torrent_manager.torrent:
            speed = write_size(WebsocketController.program.torrent_manager.torrent.download_counter.value)
            ready = WebsocketController.program.torrent_manager.torrent.bytes_ready_in_buffer
            torrent_state = WebsocketController.program.torrent_manager.torrent.state
            connected_peers = len(WebsocketController.program.torrent_manager.torrent.peer_manager.connected_peers)
            potential_peers = len(WebsocketController.program.torrent_manager.torrent.peer_manager.potential_peers)

        return Status(speed, ready, psutil.cpu_percent(), psutil.virtual_memory().percent, torrent_state, connected_peers, potential_peers)

    @staticmethod
    def get_player_data():
        state = WebsocketController.program.gui_manager.player.state

        if not WebsocketController.program.gui_manager.player.prepared:
            if state == PlayerState.Nothing or state == PlayerState.Ended:
                return CurrentMedia(0, None, None, None, None, 0, 0, 100, 0, 0, [], 0, False, [], 0, 0)

        if state == PlayerState.Nothing or state == PlayerState.Ended:
            state = PlayerState.Opening

        title = WebsocketController.program.gui_manager.player.title
        percentage = 0
        if WebsocketController.program.torrent_manager.torrent is not None and WebsocketController.program.torrent_manager.torrent.media_file is not None:
            buffered = WebsocketController.program.torrent_manager.torrent.bytes_ready_in_buffer
            percentage = buffered / WebsocketController.program.torrent_manager.torrent.media_file.length * 100
            if WebsocketController.program.torrent_manager.torrent.state == TorrentState.Done:
                percentage = 100

        media = CurrentMedia(state.value,
                             WebsocketController.program.gui_manager.player.type,
                             title,
                             WebsocketController.program.gui_manager.player.path,
                             WebsocketController.program.gui_manager.player.img,
                             WebsocketController.program.gui_manager.player.get_position(),
                             WebsocketController.program.gui_manager.player.get_length(),
                             WebsocketController.program.gui_manager.player.get_volume(),
                             WebsocketController.program.gui_manager.player.get_length(),
                             WebsocketController.program.gui_manager.player.get_selected_sub(),
                             WebsocketController.program.gui_manager.player.get_subtitle_tracks(),
                             WebsocketController.program.gui_manager.player.get_subtitle_delay() / 1000 / 1000,
                             True,
                             WebsocketController.program.gui_manager.player.get_audio_tracks(),
                             WebsocketController.program.gui_manager.player.get_audio_track(),
                             percentage)
        return media

    @staticmethod
    def get_media_data():
        torrent = WebsocketController.program.torrent_manager.torrent
        if torrent is None:
            de = MediaInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ThreadManager.thread_count(), 0, 0)
        else:
            de = MediaInfo(len(torrent.peer_manager.potential_peers),
                           len(torrent.peer_manager.connected_peers),
                           torrent.total_size,
                           torrent.download_counter.total,
                           torrent.download_counter.value,
                           torrent.bytes_ready_in_buffer,
                           torrent.bytes_total_in_buffer,
                           torrent.bytes_streamed,
                           torrent.state,
                           torrent.stream_position,
                           torrent.stream_buffer_position,
                           ThreadManager.thread_count(),
                           torrent.left,
                           torrent.overhead)

        if Settings.get_bool("dht"):
            de.add_dht(WebsocketController.program.torrent_manager.dht.routing_table.count_nodes())

        return de