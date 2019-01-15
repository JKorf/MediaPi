import json
import traceback
from threading import Lock

from Database.Database import Database
from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.State import StateManager
from Shared.Util import to_JSON, Singleton
from Webserver.Controllers.Websocket.PendingMessagesHandler import PendingMessagesHandler, ClientMessage
from Webserver.Models import WebSocketResponseMessage, WebSocketUpdateMessage, WebSocketSlaveCommand, WebSocketRequestMessage, WebSocketInvalidMessage, WebSocketSlaveResponse


class MasterWebsocketController(metaclass=Singleton):

    def __init__(self):
        self.clients = dict()
        self.slaves = SlaveCollection()
        self.pending_message_handler = PendingMessagesHandler(
            lambda msg: self.broadcast_info(msg.id, msg.type, msg.data),
            self.client_message_invalid,
            self.client_message_removed)

        self._ws_lock = Lock()
        self.last_id = 0
        self.last_id_lock = Lock()
        self.instance_name = Settings.get_string("name")

        self.own_slave = SlaveClient(self.next_id(), self.instance_name, None)
        self.own_slave.update_data("player", VLCPlayer().player_state)
        self.own_slave.update_data("media", MediaManager().media_data)
        self.own_slave.update_data("torrent", MediaManager().torrent_data)
        self.own_slave.update_data("state", StateManager().state_data)
        self.slaves.add_slave(self.own_slave)

        EventManager.register_event(EventType.ClientRequest, self.add_client_request)

    def is_self(self, id):
        return self.own_slave.id == id

    def start(self):
        StateManager().state_data.register_callback(lambda x: self.slave_update(self.own_slave, "state", x))
        VLCPlayer().player_state.register_callback(lambda x: self.slave_update(self.own_slave, "player", x))
        MediaManager().media_data.register_callback(lambda x: self.slave_update(self.own_slave, "media", x))
        MediaManager().torrent_data.register_callback(lambda x: self.slave_update(self.own_slave, "torrent", x))
        self.slaves.register_callback(lambda x: self.update_slaves_data(x.data))

    def add_client_request(self, callback, valid_for, type, data):
        self.pending_message_handler.add_pending_message(ClientMessage(self.next_id(), callback, valid_for, type, data))

    def client_message_invalid(self, msg):
        for client, subs in list(self.clients.items()):
            self.write_message(client, WebSocketInvalidMessage(msg.id, msg.type))

    def client_message_removed(self, msg, by_client):
        for client, subs in list(self.clients.items()):
            if client is by_client:
                continue

            self.write_message(client, WebSocketInvalidMessage(msg.id, msg.type))

    def slave_update(self, slave, type, data):
        slave.update_data(type, data)
        self.broadcast(str(slave.id) + "." + type, data)

    def update_slaves_data(self, data):
        Logger.write(2, "Slave update broadcast")
        self.broadcast("slaves", data)

    def trigger_initial_data(self, client, id, subscription):
        msg = WebSocketUpdateMessage(id, None)
        if "." in subscription.topic:
            instance = int(subscription.topic.split(".")[0])
            topic = subscription.topic.split(".")[1]

            slave = self.slaves.get_slave_by_id(instance)
            if slave is None:
                return

            msg.data = slave.get_data(topic)
        else:
            if subscription.topic == "slaves":
                msg.data = self.slaves.data

        self.write_message(client, msg)

    def opening_client(self, client):
        if client not in self.clients:
            Logger.write(2, "New connection")

    def client_message(self, client, msg):
        data = json.loads(msg)
        if 'event' in data and data['event'] == 'init':
            if data['type'] == 'Slave':
                self.slaves.add_slave(SlaveClient(self.next_id(), data['data'], client))
                Logger.write(2, "Slave initialized: " + data['data'])
            elif data['type'] == 'UI':
                self.clients[client] = []
                Logger.write(2, "UI client initialized")
                for message in self.pending_message_handler.get_pending_for_new_client():
                    self.write_message(client, WebSocketRequestMessage(message.id, self.own_slave.id, message.type, message.data))

        if client in self.clients:
            self.ui_client_message(client, data)
        else:
            self.slave_client_message(client, data)

    def ui_client_message(self, client, data):
        if data['event'] == 'subscribe':
            request_id = int(data['request_id'])
            id = self.next_id()
            subscription = Subscription(id, data['topic'])
            self.clients[client].append(subscription)
            Logger.write(2, "Client subscribed to " + str(data['topic']))
            self.write_message(client, WebSocketResponseMessage(request_id, [subscription.id]))
            self.trigger_initial_data(client, id, subscription)

        elif data['event'] == 'unsubscribe':
            request_id = int(data['request_id'])
            self.clients[client] = [x for x in self.clients[client] if x.id != request_id]
            Logger.write(2, "Client unsubscribed from " + str(data['topic']))

        elif data['event'] == 'response':
            id = int(data['response_id'])
            instance_id = int(data['instance_id'])
            if instance_id == self.own_slave.id:
                msg = self.pending_message_handler.get_message_by_response_id(id)
                if msg is None:
                    Logger.write(2, "Received response on request not pending")
                    return

                self.pending_message_handler.remove_client_message(msg, client)
                Logger.write(2, "Client message response on " + str(id) +", data: " + str(data['data']))
                msg.callback(data['data'])
            else:
                slave = self.slaves.get_slave_by_id(instance_id)
                self.write_message(slave._client, data)

    def slave_client_message(self, client, data):
        slave = [x for x in self.slaves.data if x._client == client][0]
        if 'event' in data and data['event'] == 'update':
            self.slave_update(slave, data['topic'], data['data'])
            Logger.write(1, "Slave update: " + data['topic'])

        if 'type' in data and (data['type'] == 'request' or data['type'] == 'invalid'):
            Logger.write(2, "Slave client request: " + data['info_type'])
            data['instance_id'] = slave.id
            for client, subs in list(self.clients.items()):
                self.write_message(client, data)

        if 'event' in data and data['event'] == 'master_request':
            if data['type'] == 'database':
                method = getattr(Database(), data['method'])
                method(*data['parameters'])
                Logger.write(2, "Slave db update: " + str(data))
            elif data['type'] == 'subtitles':
                Logger.write(2, "Slave subtitle request: " + str(data))
                sub_data = MediaManager().subtitle_provider.search_subtitles_for_file(data['parameters'][0])
                self.write_message(client, WebSocketSlaveResponse(data['type'], data['method'], sub_data))

    def closing_client(self, client):
        if client in self.clients:
            Logger.write(2, "Connection closed")
            del self.clients[client]

        slave = [x for x in self.slaves.data if x._client == client]
        if len(slave) > 0:
            Logger.write(2, "Slave " + slave[0].name + " disconnected")
            self.slaves.remove_slave(slave[0])

    def broadcast(self, topic, data=None):
        for client, subs in list(self.clients.items()):
            for sub in [x for x in subs if x.topic == topic]:
                self.write_message(client, WebSocketUpdateMessage(sub.id, data))

    def broadcast_info(self, id, info_type, data=None):
        for client, subs in list(self.clients.items()):
            self.write_message(client, WebSocketRequestMessage(id, self.own_slave.id, info_type, data))

    def write_message(self, client, websocket_message):
        with self._ws_lock:
            try:
                client.write_message(to_JSON(websocket_message))
            except:
                Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    def send_to_slave(self, slave_id, topic, method, parameters):
        slave = self.slaves.get_slave_by_id(slave_id)
        if slave is None:
            Logger.write(2, "Can't send to slave, slave not found")
            return

        self.write_message(slave._client, WebSocketSlaveCommand(topic, method, parameters))

    def next_id(self):
        with self.last_id_lock:
            self.last_id += 1
            return self.last_id

class Subscription:

    def __init__(self, id, topic):
        self.id = id
        self.topic = topic

class SlaveClient:

    def __init__(self, id, name, client):
        self.id = id
        self.name = name
        self._client = client
        self.last_seen = 0
        self._data_registrations = dict()
        self._data_registrations["player"] = DataRegistration()
        self._data_registrations["media"] = DataRegistration()
        self._data_registrations["torrent"] = DataRegistration()
        self._data_registrations["state"] = DataRegistration()

    def update_data(self, name, data):
        self._data_registrations[name].data = data

    def get_data(self, name):
        return self._data_registrations[name].data


class SlaveCollection(Observable):

    def __init__(self):
        super().__init__("slaves", 1)
        self.data = []

    def add_slave(self, slave):
        self.start_update()
        self.data.append(slave)
        self.stop_update()

    def remove_slave(self, slave):
        self.start_update()
        self.data.remove(slave)
        self.stop_update()

    def get_slave(self, name):
        slave = [x for x in self.data if x.name == name]
        if len(slave) > 0:
            return slave[0]
        return None

    def get_slave_by_id(self, id):
        slave = [x for x in self.data if x.id == id]
        if len(slave) > 0:
            return slave[0]
        return None

class DataRegistration:

    def __init__(self):
        self.last_change = 0
        self.data = None
