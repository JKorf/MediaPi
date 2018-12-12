import asyncio
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
from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, WebSocketMessage, Status, CurrentMedia, MediaInfo


class SlaveWebsocketController:

    def __init__(self):
        self.server_socket = None
        self.server_connect_engine = Engine("Server socket connect", 10000)
        self.server_connect_engine.add_work_item("Check connection", 10000, self.test)
        self.instance_name = Settings.get_string("name")

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.broadcast_player_data(x))
        MediaManager().mediaData.register_callback(lambda x: self.broadcast_media_data(x))

        self.server_connect_engine.start()

    def test(self):
        asyncio.run(self.check_master_connection())

        # loop = asyncio.get_event_loop()
        # tasks = [
        #     asyncio.ensure_future(self.check_master_connection()),
        # ]
        # loop.run_until_complete(asyncio.wait(tasks))
        # loop.close()

    async def check_master_connection(self):
        if self.server_socket is None:
            Logger.write(2, "Connecting server socket")
            await websocket_connect("ws://192.168.0.159/ws", callback=self.connect_callback, on_message_callback=self.on_master_message, connect_timeout=0.5)
            a = ""

    def connect_callback(self, connect_result):
        self.server_socket = connect_result.result()
        self.server_socket.write_message(to_JSON(WebSocketMessage(0, "slave_init", "slave_init", [self.instance_name])))
        self.broadcast_player_data(VLCPlayer().playerState)
        self.broadcast_media_data(MediaManager().mediaData)

    def on_master_message(self, raw_data):
        if raw_data is None:
            self.server_socket = None
            return

        data = json.loads(raw_data)
        if data['event'] == 'command':
            if data['type'] == 'play_file':
                MediaManager().start_file(data['data'][0], 0)

    def broadcast_player_data(self, data):
        if not self.server_socket:
            return

        Logger.write(2, "Sending player update to server socket")
        self.server_socket.write_message(to_JSON(WebSocketMessage(0, "player", "slave_data", data)))

    def broadcast_media_data(self, data):
        if not self.server_socket:
            return

        Logger.write(2, "Sending media update to server socket")
        self.server_socket.write_message(to_JSON(WebSocketMessage(0, "media", "slave_data", data)))