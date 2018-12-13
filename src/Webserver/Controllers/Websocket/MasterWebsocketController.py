import json
import time
import traceback
from threading import Lock

import psutil
from tornado import websocket
from tornado.websocket import websocket_connect

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import PlayerState, VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from MediaPlayer.Util.Enums import TorrentState
from Shared.Engine import Engine
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, Status, CurrentMedia, MediaInfo, WebSocketResponseMessage, WebSocketUpdateMessage


class MasterWebsocketController:

    def __init__(self):
        self.clients = dict()
        self.slaves = SlaveCollection()

        self._ws_lock = Lock()
        self.last_id = 0
        self.last_id_lock = Lock()
        self.instance_name = Settings.get_string("name")

        self.own_slave = SlaveClient(self.instance_name, None)
        self.own_slave.player_state = VLCPlayer().playerState
        self.own_slave.media_data = MediaManager().mediaData
        self.slaves.add_slave(self.own_slave)

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.slave_update(self.own_slave, "player", x))
        MediaManager().mediaData.register_callback(lambda x: self.slave_update(self.own_slave, "media", x))
        self.slaves.register_callback(lambda x: self.update_slaves_data(x.data))

    def slave_update(self, slave, type, data):
        if type == "player":
            slave.player_state = data
            self.update_player_data(slave.name, data)
        if type == "media":
            slave.media_data = data
            self.update_media_data(slave.name, data)

    def update_slaves_data(self, data):
        Logger.write(2, "Slave update broadcast")
        self.broadcast("slaves", data)

    def update_player_data(self, instance, data):
        self.broadcast(instance + ".player", data)

    def update_media_data(self, instance, data):
        self.broadcast(instance + ".media", data)

    def trigger_initial_data(self, client, subscription):
        if subscription.topic.endswith(".player"):
            slave = [x for x in self.slaves.data if subscription.topic == x.name + ".player"][0]
            self.update_player_data(slave.name, slave.player_state)
        elif subscription.topic.endswith(".media"):
            slave = [x for x in self.slaves.data if subscription.topic == x.name + ".media"][0]
            self.update_media_data(slave.name, slave.media_data)
        elif subscription.topic == "slaves":
            self.update_slaves_data(self.slaves.data)

    def opening_client(self, client):
        if client not in self.clients:
            Logger.write(2, "New connection")

    def client_message(self, client, msg):
        data = json.loads(msg)
        if data['event'] == 'init':
            if data['type'] == 'Slave':
                self.slaves.add_slave(SlaveClient(data['data'], client))
                Logger.write(2, "Slave initialized: " + data['data'])
            elif data['type'] == 'UI':
                self.clients[client] = []
                Logger.write(2, "UI client initialized")

        if data['event'] == 'subscribe':
            request_id = int(data['request_id'])
            with self.last_id_lock:
                self.last_id += 1
                id = self.last_id
            subscription = Subscription(id, data['topic'])
            self.clients[client].append(subscription)
            Logger.write(2, "Client subscribed to " + str(data['topic']))
            self.write_message(client, WebSocketResponseMessage(request_id, [subscription.id]))
            self.trigger_initial_data(client, subscription)

        elif data['event'] == 'unsubscribe':
            request_id = int(data['request_id'])
            self.clients[client] = [x for x in self.clients[client] if x.id != request_id]
            Logger.write(2, "Client unsubscribed from " + str(data['topic']))

        elif data['event'] == 'update':
            slave = [x for x in self.slaves.data if x._client == client][0]
            self.slave_update(slave, data['topic'], data['data'])
            Logger.write(2, "Slave update: " + data['topic'])

    def closing_client(self, client):
        if client in self.clients:
            Logger.write(2, "Connection closed")
            del self.clients[client]

        slave = [x for x in self.slaves.data if x._client == client]
        if len(slave) > 0:
            Logger.write(2, "Slave " + slave[0].name + " disconnected")
            self.slaves.remove_slave(slave[0])

    def broadcast(self, topic, data=None):
        for client, subs in self.clients.items():
            for sub in [x for x in subs if x.topic == topic]:
                self.write_message(client, WebSocketUpdateMessage(sub.id, data))

    def write_message(self, client, websocket_message):
        with self._ws_lock:
            try:
                client.write_message(to_JSON(websocket_message))
            except:
                Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    def play_slave_file(self, slave_name, path):
        slave = [x for x in self.slaves if x.name == slave_name][0]
        #slave.client.write_message(to_JSON(WebSocketMessage("command", "play_file", [path])))


class Subscription:

    def __init__(self, id, topic):
        self.id = id
        self.topic = topic

class SlaveClient:

    def __init__(self, name, client):
        self.name = name
        self._client = client
        self.last_seen = 0

        self.player_state = None
        self.media_data = None

class SlaveCollection(Observable):

    def __init__(self):
        super().__init__("slaves", 1)
        self.data = []

    def add_slave(self, slave):
        self.data.append(slave)
        self.updated()

    def remove_slave(self, slave):
        self.data.remove(slave)
        self.updated()