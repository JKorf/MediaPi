import json
import time
import traceback
from threading import Lock

import psutil

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from MediaPlayer.Util.Enums import TorrentState
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, WebSocketMessage, Status, CurrentMedia, MediaInfo


class SyncWebsocketController:
    server_socket = None

    @staticmethod
    def init():
        VLCPlayer().playerState.register_callback(lambda x: SyncWebsocketController.broadcast_player_data(x))
        MediaManager().mediaData.register_callback(lambda x: SyncWebsocketController.broadcast_media_data(x))

    @staticmethod
    def broadcast_player_data(data):
        if not SyncWebsocketController.server_socket:
            return

        SyncWebsocketController.server_socket.write_message(to_JSON(WebSocketMessage(0, "notify", "player", data)))

    @staticmethod
    def broadcast_media_data(data):
        if not SyncWebsocketController.server_socket:
            return

        SyncWebsocketController.server_socket.write_message(to_JSON(WebSocketMessage(0, "notify", "media", data)))

    @staticmethod
    def opening_client(client):
        Logger.write(2, "Server socket connected")
        SyncWebsocketController.server_socket = client

    @staticmethod
    def client_message(client, msg):
        pass

    @staticmethod
    def closing_client(client):
        Logger.write(2, "Server socket disconnected")
        SyncWebsocketController.server_socket = None