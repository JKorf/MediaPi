import json
import time
import traceback
from threading import Lock

import psutil
from tornado.websocket import websocket_connect

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


class SlaveWebsocketController:
    server_socket = None

    @staticmethod
    def init():
        VLCPlayer().playerState.register_callback(lambda x: SlaveWebsocketController.broadcast_player_data(x))
        MediaManager().mediaData.register_callback(lambda x: SlaveWebsocketController.broadcast_media_data(x))

        Logger.write(2, "Connecting server socket")
        websocket_connect("ws://127.0.0.1/ws", callback=SlaveWebsocketController.connect_callback, on_message_callback=SlaveWebsocketController.on_master_message)

    @staticmethod
    def connect_callback(a):
        SlaveWebsocketController.server_socket = a.result()
        SlaveWebsocketController.server_socket.write_message(to_JSON(WebSocketMessage(0, "slave_init", "slave_init", ["Slaapkamer"])))
        SlaveWebsocketController.broadcast_player_data(VLCPlayer().playerState)
        SlaveWebsocketController.broadcast_media_data(MediaManager().mediaData)

    @staticmethod
    def on_master_message(raw_data):
        data = json.loads(raw_data)
        if data['event'] == 'command':
            if data['type'] == 'play_file':
                MediaManager().start_file(data['data'][0], 0)


    @staticmethod
    def broadcast_player_data(data):
        if not SlaveWebsocketController.server_socket:
            return

        Logger.write(2, "Sending player update to server socket")
        SlaveWebsocketController.server_socket.write_message(to_JSON(WebSocketMessage(0, "player", "slave_data", data)))


    @staticmethod
    def broadcast_media_data(data):
        if not SlaveWebsocketController.server_socket:
            return

        Logger.write(2, "Sending media update to server socket")
        SlaveWebsocketController.server_socket.write_message(to_JSON(WebSocketMessage(0, "media", "slave_data", data)))

    @staticmethod
    def opening_client(client):
        Logger.write(2, "Server socket connected")
        SlaveWebsocketController.server_socket = client

    @staticmethod
    def client_message(client, msg):
        pass

    @staticmethod
    def closing_client(client):
        Logger.write(2, "Server socket disconnected")
        SlaveWebsocketController.server_socket = None