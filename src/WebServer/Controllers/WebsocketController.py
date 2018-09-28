from threading import Lock

from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from WebServer.Models import MediaFile, WebSocketMessage


class WebsocketController:

    clients = []
    _ws_lock = Lock()
    program = None

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

                WebsocketController.broadcast('request', 'media_selection', files)

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
                client.write_message(to_JSON(WebSocketMessage(event, method, parameters)))

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