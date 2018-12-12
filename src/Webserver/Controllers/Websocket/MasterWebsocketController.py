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
from Shared.Settings import Settings
from Shared.Threading import CustomThread, ThreadManager
from Shared.Util import to_JSON, write_size
from Webserver.Models import MediaFile, WebSocketMessage, Status, CurrentMedia, MediaInfo


class MasterWebsocketController:

    def __init__(self):
        self.clients = dict()
        self._ws_lock = Lock()
        self.last_id = 0
        self.last_id_lock = Lock()
        self.slaves = []
        self.instance_name = Settings.get_string("name")

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.update_player_data(self.instance_name, x))
        MediaManager().mediaData.register_callback(lambda x: self.update_media_data(self.instance_name, x))

    def slave_update(self, slave, type, data):
        if type == "player":
            slave.player_data = data
            self.update_player_data(slave.name, data)
        if type == "media":
            slave.media_data = data
            self.update_media_data(slave.name, data)

    def update_player_data(self, instance, data):
        self.notify("player", [instance], data)

    def update_media_data(self, instance, data):
        self.notify("media", [instance], data)

    def update_data(self, topic, instance, player_data, media_data):
        if topic == "player":
            self.update_player_data(instance, player_data)
        elif topic == "media":
            self.update_media_data(instance, media_data)

    def trigger_initial_data(self, client, subscription):
        instance = subscription.params[0]
        if instance == self.instance_name:
            self.update_data(subscription.topic, self.instance_name, VLCPlayer().playerState, MediaManager().mediaData)
        else:
            slave = [x for x in self.slaves if x.name == instance]
            if len(client) == 0:
                Logger.write(2, instance + " not in slave list")
                return
            self.update_data(subscription.topic, slave[0].name, slave[0].player_state, slave[0].media_data)

    def opening_client(self, client):
        if client not in self.clients:
            Logger.write(2, "New connection")
            self.clients[client] = []

    def client_message(self, client, msg):
        data = json.loads(msg)
        request_id = int(data['id'])

        if data['event'] == 'subscribe':
            with self.last_id_lock:
                self.last_id += 1
                id = self.last_id
            subscription = Subscription(id, data['topic'], data['params'])
            self.clients[client].append(subscription)
            Logger.write(2, "Client subscribed to " + str(data['topic']))
            client.write_message(to_JSON(WebSocketMessage(request_id, "response", "subscribed", [subscription.id])))
            self.trigger_initial_data(client, subscription)

        elif data['event'] == 'unsubscribe':
            self.clients[client] = [x for x in self.clients[client] if x.id == request_id]
            Logger.write(2, "Client unsubscribed from " + str(data['topic']))

        elif data['event'] == 'slave_init':
            self.slaves.append(SlaveClient(data['data'][0], client))
            Logger.write(2, "Slave initialized: " + data['data'][0])

        elif data['event'] == 'slave_data':
            slave = [x for x in self.slaves if x.client == client][0]
            self.slave_update(slave, data['type'], data['data'])
            Logger.write(2, "Slave update: " + data['type'])

    def closing_client(self, client):
        if client in self.clients:
            Logger.write(2, "Connection closed")
            del self.clients[client]
            self.slaves = [x for x in self.slaves if x.client != client]

    def notify(self, subscription, sub_params, data=None):
        for client, subs in self.clients.items():
            for sub in [x for x in subs if x.matches(subscription, sub_params)]:
                self.write_message(client, sub.id, "notify", "update", data)

    def notify_client(self, client, id, data):
        self.write_message(client, id, "notify", "update", data)

    def write_message(self, client, id, type, event, data):
        if data is None:
            data = ""

        with self._ws_lock:
            try:
                client.write_message(to_JSON(WebSocketMessage(id, type, event, data)))
            except:
                Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    def play_slave_file(self, slave_name, path):
        slave = [x for x in self.slaves if x.name == slave_name][0]
        slave.client.write_message(to_JSON(WebSocketMessage(0, "command", "play_file", [path])))


class Subscription:

    def __init__(self, id, topic, params):
        self.id = id
        self.topic = topic
        self.params = params

    def matches(self, topic, params):
        return self.topic == topic and self.params == params


class SlaveClient:

    def __init__(self, name, client):
        self.name = name
        self.client = client
        self.last_seen = 0

        self.player_state = None
        self.media_data = None
