import json
import traceback
from threading import Lock

import time

from MediaPlayer.Player.VLCPlayer import VLCPlayer
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Observable import Observable
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import to_JSON, Singleton, current_time
from Webserver.Models import WebSocketResponseMessage, WebSocketUpdateMessage, WebSocketSlaveCommand, WebSocketRequestMessage, WebSocketInvalidMessage


class MasterWebsocketController(metaclass=Singleton):

    def __init__(self):
        self.clients = dict()
        self.slaves = SlaveCollection()
        self.pending_messages = []

        self._ws_lock = Lock()
        self.last_id = 0
        self.last_id_lock = Lock()
        self.instance_name = Settings.get_string("name")

        self.own_slave = SlaveClient(self.next_id(), self.instance_name, None)
        self.own_slave.update_data("player", VLCPlayer().playerState)
        self.own_slave.update_data("media", MediaManager().mediaData)
        self.slaves.add_slave(self.own_slave)

        self.pending_message_thread = CustomThread(self.check_pending_messages, "Check pending messages")

        EventManager.register_event(EventType.ClientRequest, self.add_client_request)

    def is_self(self, id):
        return self.own_slave.id == id

    def start(self):
        VLCPlayer().playerState.register_callback(lambda x: self.slave_update(self.own_slave, "player", x))
        MediaManager().mediaData.register_callback(lambda x: self.slave_update(self.own_slave, "media", x))
        self.slaves.register_callback(lambda x: self.update_slaves_data(x.data))
        self.pending_message_thread.start()

    def add_client_request(self, callback, valid_for, type, data):
        id = self.next_id()
        if valid_for > 0:
            self.pending_messages.append(ClientMessage(id, callback, valid_for, type, data))
        self.broadcast_info(id, type, data)

    def check_pending_messages(self):
        while True:
            check_time = current_time()
            invalid = [x for x in self.pending_messages if x.valid_till < check_time]
            for msg in invalid:
                Logger.write(2, "Timing out message " + str(msg.id))
                self.remove_client_message(msg)
            time.sleep(1)

    def remove_client_message(self, msg, exclude_client=None):
        self.pending_messages = [x for x in self.pending_messages if x.id != msg.id]
        for client, subs in self.clients.items():
            if client is exclude_client:
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
        if data['event'] == 'init':
            if data['type'] == 'Slave':
                self.slaves.add_slave(SlaveClient(self.next_id(), data['data'], client))
                Logger.write(2, "Slave initialized: " + data['data'])
            elif data['type'] == 'UI':
                self.clients[client] = []
                Logger.write(2, "UI client initialized")
                for message in self.pending_messages:
                    self.write_message(client, WebSocketRequestMessage(message.id, message.type, message.data))

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
            msg = [x for x in self.pending_messages if x.id == id]
            if len(msg) == 0:
                Logger.write(2, "Received response on request not pending")
                return

            self.remove_client_message(msg[0], client)
            Logger.write(2, "Client message response on " + str(id) +", data: " + str(data['data']))
            msg[0].callback(data['data'])

    def slave_client_message(self, client, data):
        if data['event'] == 'update':
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

    def broadcast_info(self, id, info_type, data=None):
        for client, subs in self.clients.items():
            self.write_message(client, WebSocketRequestMessage(id, info_type, data))

    def write_message(self, client, websocket_message):
        with self._ws_lock:
            try:
                client.write_message(to_JSON(websocket_message))
            except:
                Logger.write(2, "Failed to send msg to client because client is closed: " + traceback.format_exc())

    def send_to_slave(self, slave_id, command, parameters):
        slave = self.slaves.get_slave_by_id(slave_id)
        if slave is None:
            Logger.write(2, "Can't send to slave, slave not found")
            return

        self.write_message(slave._client, WebSocketSlaveCommand(command, parameters))

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

    def update_data(self, name, data):
        self._data_registrations[name].data = data

    def get_data(self, name):
        return self._data_registrations[name].data


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

class ClientMessage:

    def __init__(self, id, callback, valid_for, type, data):
        self.id = id
        self.callback = callback
        self.valid_till = current_time() + valid_for
        self.type = type
        self.data = data