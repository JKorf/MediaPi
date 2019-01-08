import json
from threading import Lock

import websocket
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Controllers.Websocket.PendingMessagesHandler import PendingMessagesHandler, ClientMessage
from Webserver.Models import WebSocketInitMessage, WebSocketSlaveMessage, WebSocketSlaveRequest, WebSocketRequestMessage, WebSocketInvalidMessage


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
        self.last_id = 0
        self.last_id_lock = Lock()

        self.pending_message_handler = PendingMessagesHandler(self.send_client_request, self.client_message_invalid, self.client_message_removed)

        EventManager.register_event(EventType.ClientRequest, self.add_client_request)

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.broadcast_player_data(x))
        MediaManager().mediaData.register_callback(lambda x: self.broadcast_media_data(x))

        self.server_connect_engine.start()

    def add_client_request(self, callback, valid_for, type, data):
        self.pending_message_handler.add_pending_message(ClientMessage(self.next_id(), callback, valid_for, type, data))

    def send_client_request(self, msg):
        if self.connected:
            self.write(WebSocketRequestMessage(msg.id, 0, msg.type, msg.data))

    def client_message_invalid(self, msg):
        if self.connected:
            self.write(WebSocketInvalidMessage(msg.id, msg.type))

    def client_message_removed(self, msg, by_client):
        pass

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
        self.connected = True
        self.write(WebSocketInitMessage(self.instance_name))
        self.broadcast_player_data(VLCPlayer().playerState)
        self.broadcast_media_data(MediaManager().mediaData)

        pending = self.pending_message_handler.get_pending_for_new_client()
        for msg in pending:
            self.write(WebSocketRequestMessage(msg.id, 0, msg.type, msg.data))

    def on_master_message(self, raw_data):
        Logger.write(2, "Received master message: " + raw_data)
        data = json.loads(raw_data)
        if data['event'] == 'response':
            msg = self.pending_message_handler.get_message_by_response_id(int(data['response_id']))
            if msg is None:
                Logger.write(2, "Received response on request not pending")
                return

            self.pending_message_handler.remove_client_message(msg, None)
            Logger.write(2, "Client message response on " + str(id) + ", data: " + str(data['data']))
            msg.callback(data['data'])

        elif data['event'] == 'command':
            if data['topic'] == 'play_file':
                MediaManager().start_file(*data['parameters'])
            elif data['topic'] == "play_movie":
                MediaManager().start_movie(*data['parameters'])
            elif data['topic'] == "play_episode":
                MediaManager().start_episode(*data['parameters'])
            elif data['topic'] == "play_torrent":
                MediaManager().start_torrent(*data['parameters'])
            elif data['topic'] == "play_radio":
                MediaManager().start_radio(*data['parameters'])
            elif data['topic'] == "play_url":
                MediaManager().start_url(*data['parameters'])
            elif data['topic'] == 'play_stop':
                MediaManager().stop_play()
            elif data['topic'] == 'pause_resume':
                MediaManager().pause_resume()

    def broadcast_player_data(self, data):
        if not self.connected:
            return

        self.write(WebSocketSlaveMessage("player", data))

    def broadcast_media_data(self, data):
        if not self.connected:
            return

        self.write(WebSocketSlaveMessage("media", data))

    def write(self, data):
        json = to_JSON(data)
        Logger.write(2, "Sending to master: " + json)
        self.server_socket.send(json)


    def next_id(self):
        with self.last_id_lock:
            self.last_id += 1
            return self.last_id