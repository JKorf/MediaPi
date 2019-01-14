import json
import traceback
from threading import Lock

import websocket
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.State import StateManager
from Shared.Util import to_JSON
from Webserver.Controllers.Websocket.PendingMessagesHandler import PendingMessagesHandler, ClientMessage
from Webserver.Models import WebSocketInitMessage, WebSocketSlaveMessage, WebSocketRequestMessage, WebSocketInvalidMessage, WebSocketDatabaseMessage


class SlaveWebsocketController:

    def __init__(self):
        self.server_socket = websocket.WebSocketApp(Settings.get_string("master_ip").replace("http://", "ws://") + "/ws",
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
        EventManager.register_event(EventType.DatabaseUpdate, lambda method, params: self.write(WebSocketDatabaseMessage(method, params)))

    def start(self):
        VLCPlayer().player_state.register_callback(lambda x: self.broadcast_data("player", x))
        MediaManager().media_data.register_callback(lambda x: self.broadcast_data("media", x))
        MediaManager().torrent_data.register_callback(lambda x: self.broadcast_data("torrent", x))
        StateManager().state_data.register_callback(lambda x: self.broadcast_data("state", x))

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
        self.broadcast_data("player", VLCPlayer().player_state)
        self.broadcast_data("media", MediaManager().media_data)
        self.broadcast_data("torrent", MediaManager().torrent_data)
        self.broadcast_data("state", StateManager().state_data)

        pending = self.pending_message_handler.get_pending_for_new_client()
        for msg in pending:
            self.write(WebSocketRequestMessage(msg.id, 0, msg.type, msg.data))

    def on_master_message(self, raw_data):
        try:
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
                if data['topic'] == 'media':
                    method = getattr(MediaManager(), data['method'])
                    method(*data['parameters'])
        except Exception as e:
            Logger.write(3, "Error in Slave websocket controoler: " + str(e), 'error')
            stack_trace = traceback.format_exc().split('\n')
            for stack_line in stack_trace:
                Logger.write(3, stack_line)

    def broadcast_data(self, type, data):
        if not self.connected:
            return

        self.write(WebSocketSlaveMessage(type, data))


    def write(self, data):
        json = to_JSON(data)
        Logger.write(1, "Sending to master: " + json)
        self.server_socket.send(json)


    def next_id(self):
        with self.last_id_lock:
            self.last_id += 1
            return self.last_id