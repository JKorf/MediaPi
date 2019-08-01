import base64
import json

from flask import request
from flask_socketio import disconnect

from Database.Database import Database
from MediaPlayer.Util.Util import get_file_info
from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import SecureSettings
from Shared.Util import current_time, to_JSON
from Webserver.APIController import socketio, WebsocketClient, APIController, SlaveClient
from Webserver.Controllers.MediaPlayer.HDController import HDController
from Webserver.Controllers.Websocket2.BaseWebsocketController import BaseWebsocketController
from Webserver.Controllers.Websocket2.UIWebsocketController import UIWebsocketController


class SlaveWebsocketController(BaseWebsocketController):

    @staticmethod
    def on_connect():
        Logger().write(LogVerbosity.Info, "Slave client connected")

    @staticmethod
    def on_disconnect():
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        Logger().write(LogVerbosity.Info, "Slave client disconnected")
        if slave is None:
            return
        slave.connected = False
        APIController.slaves.changed()

    @staticmethod
    def on_init(client_name, key):
        Logger().write(LogVerbosity.Info, "Init slave: " + client_name)
        if key != SecureSettings.get_string("master_key"):
            Logger().write(LogVerbosity.Info, "Slave authentication failed")
            disconnect()
            return False

        slave = APIController.slaves.get_slave(client_name)
        if slave is not None:
            if slave.connected:
                Logger().write(LogVerbosity.Info, "Slave " + str(client_name) + " connected twice?")
                disconnect()
                return False
            else:
                Logger().write(LogVerbosity.Info, "Slave " + str(client_name) + " reconnected")
                slave.reconnect(request.sid)
                APIController.slaves.changed()
                return True

        client = WebsocketClient(request.sid, current_time())
        client.authenticated = True
        APIController.slaves.add_slave(SlaveClient(APIController.next_id(), client_name, client))
        return client.authenticated

    @staticmethod
    def on_update(topic, data):
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            Logger().write(LogVerbosity.Debug, "Slave update for not initialized slave")
            disconnect()
            return

        Logger().write(LogVerbosity.All, "Slave update " + topic + ": " + data)
        data = json.loads(data)

        slave_topic = str(slave.id) + "." + topic
        UIWebsocketController.broadcast(slave_topic, data)

    @staticmethod
    def on_notify(topic, data):
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            Logger().write(LogVerbosity.Debug, "Slave notification for not initialized slave")
            disconnect()
            return

        data = json.loads(data)
        Logger().write(LogVerbosity.Debug, "Slave notification " + topic + ": " + str(data))
        if topic == "update_watching_item":
            Database().update_watching_item(*data)

    @staticmethod
    def on_request(request_id, topic, data):
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            Logger().write(LogVerbosity.Debug, "Slave request for not initialized slave")
            disconnect()
            return

        Logger().write(LogVerbosity.Debug, "Slave request " + topic + ": " + data)
        data = json.loads(data)
        if topic == "get_directory":
            directory = to_JSON(HDController.get_directory_internal(*data))
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(directory))
            socketio.emit("response", (request_id, directory), namespace="/Slave", room=request.sid)
        elif topic == "get_history_for_url":
            history = to_JSON(Database().get_history_for_url(*data))
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(history))
            socketio.emit("response", (request_id, history), namespace="/Slave", room=request.sid)
        elif topic == "add_watched_torrent":
            history_id = Database().add_watched_torrent(*data)
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(history_id))
            socketio.emit("response", (request_id, history_id), namespace="/Slave", room=request.sid)
        elif topic == "add_watched_file":
            history_id = Database().add_watched_file(*data)
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(history_id))
            socketio.emit("response", (request_id, history_id), namespace="/Slave", room=request.sid)
        elif topic == "add_watched_url":
            history_id = Database().add_watched_url(*data)
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(history_id))
            socketio.emit("response", (request_id, history_id), namespace="/Slave", room=request.sid)
        elif topic == "add_watched_youtube":
            history_id = Database().add_watched_youtube(*data)
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(history_id))
            socketio.emit("response", (request_id, history_id), namespace="/Slave", room=request.sid)
        elif topic == "get_file_info":
            size, first_64k, last_64k = get_file_info(*data)
            Logger().write(LogVerbosity.Debug, "Slave response: " + str(size))
            encoded_first = base64.encodebytes(first_64k).decode('utf8')
            encoded_last = base64.encodebytes(last_64k).decode('utf8')
            socketio.emit("response", (request_id, size, encoded_first, encoded_last), namespace="/Slave", room=request.sid)

    @staticmethod
    def on_ui_message(title, message):
        APIController().ui_message(title, message)

    @staticmethod
    def on_ui_request(request_id, topic, data, timeout):
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            Logger().write(LogVerbosity.Debug, "Slave ui request for not initialized slave")
            disconnect()
            return

        Logger().write(LogVerbosity.Debug, "Slave ui request " + topic + ": " + data)
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        APIController().ui_request(topic, lambda *x: SlaveWebsocketController.slave_ui_request_callback(request_id, slave, x), timeout, json.loads(data))

    @staticmethod
    def slave_ui_request_callback(request_id, slave, response):
        Logger().write(LogVerbosity.Debug, "Slave ui request response id " + str(request_id) + ": " + str(response))
        socketio.emit("response", (request_id, *response), namespace="/Slave", room=slave._client.sid)

