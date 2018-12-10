import json
import time
import traceback
from threading import Lock

import psutil

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, WebSocketMessage, Status, CurrentMedia, MediaInfo


class WebsocketController:

    clients = dict()
    _ws_lock = Lock()
    # update_loop_count = 0

    @staticmethod
    def init():
        update_thread = CustomThread(WebsocketController.update_loop, "socket update loop")
        update_thread.start()


    @staticmethod
    def update_loop():
         while True:
             player_data = WebsocketController.get_player_data()
             WebsocketController.notify("player", player_data)
             time.sleep(1)

    @staticmethod
    def opening_client(client):
        if client not in WebsocketController.clients:
            Logger.write(2, "New connection")
            WebsocketController.clients[client] = []
            # if MediaManager().torrent and MediaManager().torrent.state == TorrentState.WaitingUserFileSelection:
            #     if not Settings.get_bool("slave"):
            #         watched_files = [f[9] for f in Database().get_watched_torrent_files(MediaManager().torrent.uri)]
            #         files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in [y for y in MediaManager().torrent.files if y.is_media]]
            #     else:
            #         files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in [y for y in MediaManager().torrent.files if y.is_media]]
            #
            #     client.write_message(to_JSON(WebSocketMessage('request', 'media_selection', files)))

    @staticmethod
    def client_message(client, msg):
        Logger.write(2, "Client sent " + msg)
        data = json.loads(msg)
        if data['event'] == 'subscribe':
            WebsocketController.clients[client].append(data['topic'])
            Logger.write(2, "Client subscribed to " + str(data['topic']))

    @staticmethod
    def closing_client(client):
        if client in WebsocketController.clients:
            Logger.write(2, "Connection closed")
            del WebsocketController.clients[client]

    @staticmethod
    def notify(subscription, parameters=None):
        if parameters is None:
            parameters = ""

        with WebsocketController._ws_lock:
            for client, subs in WebsocketController.clients.items():
                try:
                    if subscription in subs:
                        client.write_message(to_JSON(WebSocketMessage("notify", subscription, parameters)))
                except:
                    Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    # @staticmethod
    # def no_peers():
    #     WebsocketController.broadcast("request", "no_peers")
    #
    # @staticmethod
    # def next_episode_selection(path, name, season, episode, type, media_file, img):
    #     WebsocketController.broadcast("request", "next_episode", MediaFile(path, name, 0, season, episode, type, media_file, img, False))
    #
    # @staticmethod
    # def media_selected(file):
    #     WebsocketController.broadcast("request", "media_selection_close")
    #
    # @staticmethod
    # def media_selection_required(files):
    #     if not Settings.get_bool("slave"):
    #         watched_files = [f[9] for f in Database().get_watched_torrent_files(MediaManager().torrent.uri)]
    #         files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in files]
    #     else:
    #         files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in files]
    #     WebsocketController.broadcast("request", "media_selection", files)
    #
    # @staticmethod
    # def player_state_changed(old_state, state):
    #     WebsocketController.broadcast("player_event", "state_change", state.value)
    #
    # @staticmethod
    # def player_error():
    #     WebsocketController.broadcast("player_event", "error")
    #
    # @staticmethod
    # def player_seeking(pos):
    #     WebsocketController.broadcast("player_event", "seek", pos / 1000)
    #
    # @staticmethod
    # def player_volume(vol):
    #     WebsocketController.broadcast("player_event", "volume", vol)
    #
    # @staticmethod
    # def player_subtitle_id(id):
    #     WebsocketController.broadcast("player_event", "subtitle_id", id)
    #
    # @staticmethod
    # def player_subs_done_change(done):
    #     WebsocketController.broadcast("player_event", "subs_done_change", done)
    #
    # @staticmethod
    # def player_subtitle_offset(offset):
    #     WebsocketController.broadcast("player_event", "subtitle_offset", float(offset) / 1000 / 1000)
    #
    # @staticmethod
    # def application_error(error_type, error_message):
    #     WebsocketController.broadcast("error_event", error_type, error_message)
    #
    # @staticmethod
    # def get_status_data():
    #     speed = -1
    #     ready = -1
    #     torrent_state = -1
    #     connected_peers = -1
    #     potential_peers = -1
    #     if MediaManager().torrent:
    #         speed = write_size(MediaManager().torrent.download_counter.value)
    #         ready = MediaManager().torrent.bytes_ready_in_buffer
    #         torrent_state = MediaManager().torrent.state
    #         connected_peers = len(MediaManager().torrent.peer_manager.connected_peers)
    #         potential_peers = len(MediaManager().torrent.peer_manager.potential_peers)
    #
    #     return Status(speed, ready, psutil.cpu_percent(), psutil.virtual_memory().percent, torrent_state, connected_peers, potential_peers)
    #
    # @staticmethod
    def get_player_data():
        state = VLCPlayer().state

        if not VLCPlayer().prepared:
            if state == PlayerState.Nothing or state == PlayerState.Ended:
                return CurrentMedia(0, None, None, None, None, 0, 0, 100, 0, 0, [], 0, False, [], 0, 0)

        if state == PlayerState.Nothing or state == PlayerState.Ended:
            state = PlayerState.Opening

        title = VLCPlayer().media.title
        percentage = 0
        if MediaManager().torrent is not None and MediaManager().torrent.media_file is not None:
            buffered = MediaManager().torrent.bytes_ready_in_buffer
            percentage = buffered / MediaManager().torrent.media_file.length * 100
            if MediaManager().torrent.state == TorrentState.Done:
                percentage = 100

        media = CurrentMedia(state.value,
                             VLCPlayer().media.type,
                             title,
                             VLCPlayer().media.path,
                             VLCPlayer().media.image,
                             VLCPlayer().get_position(),
                             VLCPlayer().get_length(),
                             VLCPlayer().get_volume(),
                             VLCPlayer().get_length(),
                             VLCPlayer().get_selected_sub(),
                             VLCPlayer().get_subtitle_tracks(),
                             VLCPlayer().get_subtitle_delay() / 1000 / 1000,
                             True,
                             VLCPlayer().get_audio_tracks(),
                             VLCPlayer().get_audio_track(),
                             percentage)
        return media
    #
    # @staticmethod
    # def get_media_data():
    #     torrent = MediaManager().torrent
    #     if torrent is None:
    #         de = MediaInfo(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ThreadManager.thread_count(), 0, 0)
    #     else:
    #         de = MediaInfo(len(torrent.peer_manager.potential_peers),
    #                        len(torrent.peer_manager.connected_peers),
    #                        torrent.total_size,
    #                        torrent.download_counter.total,
    #                        torrent.download_counter.value,
    #                        torrent.bytes_ready_in_buffer,
    #                        torrent.bytes_total_in_buffer,
    #                        torrent.bytes_streamed,
    #                        torrent.state,
    #                        torrent.stream_position,
    #                        torrent.stream_buffer_position,
    #                        ThreadManager.thread_count(),
    #                        torrent.left,
    #                        torrent.overhead)
    #
    #     if Settings.get_bool("dht"):
    #         de.add_dht(len(MediaManager().dht.routing_table.all_nodes()))
    #
    #     return de