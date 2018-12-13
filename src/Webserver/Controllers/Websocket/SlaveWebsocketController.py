import asyncio
import json
import time
import traceback
from threading import Lock

import psutil
import websocket
from tornado.simple_httpclient import HTTPTimeoutError
from tornado.websocket import websocket_connect

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from MediaPlayer.Util.Enums import TorrentState
from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, Status, CurrentMedia, MediaInfo, WebSocketInitMessage, WebSocketSlaveMessage


class SlaveWebsocketController:

    def __init__(self):
        self.server_socket = websocket.WebSocketApp("ws://127.0.0.1/ws",
                                        on_message=self.on_master_message,
                                        on_close=self.on_close)
        self.server_socket.on_open = self.on_open

        self.server_connect_engine = Engine("Server socket connect", 10000)
        self.server_connect_engine.add_work_item("Check connection", 10000, self.check_master_connection)
        self.instance_name = Settings.get_string("name")
        self.connected = False

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.broadcast_player_data(x))
        MediaManager().mediaData.register_callback(lambda x: self.broadcast_media_data(x))

        self.server_connect_engine.start()

    async def check_master_connection(self):
        if not self.connected:
            Logger.write(2, "Connecting master socket")
            self.server_socket.run_forever()
            self.connected = False

        return True

    def on_close(self):
        Logger.write(2, "Master server disconnected")

    def on_open(self):
        Logger.write(2, "Connected master socket")
        self.server_socket.send(to_JSON(WebSocketInitMessage(self.instance_name)))
        self.broadcast_player_data(VLCPlayer().playerState)
        self.broadcast_media_data(MediaManager().mediaData)


    def on_master_message(self, raw_data):
        if raw_data is None:
            self.server_socket = None
            Logger.write(2, "Master server disconnected")
            return

        Logger.write(2, "Received master message: " + raw_data)
        data = json.loads(raw_data)
        if data['event'] == 'command':
            if data['topic'] == 'play_file':
                MediaManager().start_file(data['parameters'][0], 0)

    def broadcast_player_data(self, data):
        if not self.server_socket:
            return

        Logger.write(2, "Sending player update to server socket")
        self.server_socket.send(to_JSON(WebSocketSlaveMessage("player", data)))

    def broadcast_media_data(self, data):
        if not self.server_socket:
            return

        Logger.write(2, "Sending media update to server socket")
        self.server_socket.send(to_JSON(WebSocketSlaveMessage("media", data)))