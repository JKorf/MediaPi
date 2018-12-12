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

    clients = dict()
    _ws_lock = Lock()
    last_id = 0
    last_id_lock = Lock()

    slaves = []

    @staticmethod
    def init():
        VLCPlayer().playerState.register_callback(lambda x: MasterWebsocketController.update_player_data("Woonkamer", x))
        MediaManager().mediaData.register_callback(lambda x: MasterWebsocketController.update_media_data("Woonkamer", x))

    @staticmethod
    def slave_update(slave, type, data):
        if type == "player":
            MasterWebsocketController.update_player_data(slave.name, data)
        if type == "media":
            MasterWebsocketController.update_media_data(slave.name, data)

    @staticmethod
    def update_player_data(instance, data):
        MasterWebsocketController.notify("player", [instance], data)

    @staticmethod
    def update_media_data(instance, data):
        MasterWebsocketController.notify("media", [instance], data)

    @staticmethod
    def trigger_initial_data(client, subscription):
        if subscription.topic == "player":
            instance = subscription.params[0]
            if instance == "Woonkamer":
                MasterWebsocketController.notify_client(client, subscription.id, VLCPlayer().playerState)
            else:
                MasterWebsocketController.notify_client(client, subscription.id, VLCPlayer().playerState)
        if subscription.topic == "media":
            instance = subscription.params[0]
            if instance == "Woonkamer":
                MasterWebsocketController.notify_client(client, subscription.id, MediaManager().mediaData)
            else:
                MasterWebsocketController.notify_client(client, subscription.id, MediaManager().mediaData)

    @staticmethod
    def opening_client(client):
        if client not in MasterWebsocketController.clients:
            Logger.write(2, "New connection")
            MasterWebsocketController.clients[client] = []

    @staticmethod
    def client_message(client, msg):
        # Logger.write(2, "Client sent " + msg)
        data = json.loads(msg)
        request_id = int(data['id'])

        if data['event'] == 'subscribe':
            subscription = Subscription(data['topic'], data['params'])
            MasterWebsocketController.clients[client].append(subscription)
            Logger.write(2, "Client subscribed to " + str(data['topic']))
            client.write_message(to_JSON(WebSocketMessage(request_id, "response", "subscribed", [subscription.id])))
            MasterWebsocketController.trigger_initial_data(client, subscription)

        elif data['event'] == 'unsubscribe':
            MasterWebsocketController.clients[client] = [x for x in MasterWebsocketController.clients[client] if x.id == request_id]
            Logger.write(2, "Client unsubscribed from " + str(data['topic']))

        elif data['event'] == 'slave_init':
            MasterWebsocketController.slaves.append(SlaveClient(data['data'][0], client))
            Logger.write(2, "Slave initialized: " + data['data'][0])

        elif data['event'] == 'slave_data':
            slave = [x for x in MasterWebsocketController.slaves if x.client == client][0]
            MasterWebsocketController.slave_update(slave, data['type'], data['data'])
            Logger.write(2, "Slave update: " + data['type'])


    @staticmethod
    def closing_client(client):
        if client in MasterWebsocketController.clients:
            Logger.write(2, "Connection closed")
            del MasterWebsocketController.clients[client]
            MasterWebsocketController.slaves = [x for x in MasterWebsocketController.slaves if x.client != client]

    @staticmethod
    def notify(subscription, sub_params, data=None):
        if data is None:
            data = ""

        with MasterWebsocketController._ws_lock:
            for client, subs in MasterWebsocketController.clients.items():
                try:
                    for sub in [x for x in subs if x.matches(subscription, sub_params)]:
                        client.write_message(to_JSON(WebSocketMessage(sub.id, "notify", "update", data)))
                except:
                    Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    @staticmethod
    def notify_client(client, id, data):
        if data is None:
            data = ""

        with MasterWebsocketController._ws_lock:
            try:
                client.write_message(to_JSON(WebSocketMessage(id, "notify", "update", data)))
            except:
                Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    @staticmethod
    def play_slave_file(slave_name, path):
        slave = [x for x in MasterWebsocketController.slaves if x.name == slave_name][0]
        slave.client.write_message(to_JSON(WebSocketMessage(0, "command", "play_file", [path])))


class Subscription:

    def __init__(self, topic, params):
        with MasterWebsocketController.last_id_lock:
            MasterWebsocketController.last_id += 1
            self.id = MasterWebsocketController.last_id
        self.topic = topic
        self.params = params

    def matches(self, topic, params):
        return self.topic == topic and self.params == params


class SlaveClient:

    def __init__(self, name, client):
        self.name = name
        self.client = client
        self.last_seen = 0