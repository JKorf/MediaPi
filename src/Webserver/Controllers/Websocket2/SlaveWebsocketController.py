import json

from flask import request

from Database.Database import Database
from Shared.Logger import Logger, LogVerbosity
from Shared.Util import current_time, to_JSON
from Webserver.APIController import socketio, WebsocketClient, APIController, SlaveClient
from Webserver.Controllers.MediaPlayer.HDController import HDController
from Webserver.Controllers.Websocket2.UIWebsocketController import UIWebsocketController


class SlaveWebsocketController:
    @staticmethod
    def init():
        pass

    @staticmethod
    @socketio.on('connect', namespace="/Slave")
    def connected():
        Logger().write(LogVerbosity.Info, "Slave client connected")

    @staticmethod
    @socketio.on('disconnect', namespace="/Slave")
    def disconnected():
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            return
        APIController.slaves.remove_slave(slave)
        Logger().write(LogVerbosity.Info, "Slave client disconnected")

    @staticmethod
    @socketio.on('init', namespace="/Slave")
    def init_client(client_name):
        Logger().write(LogVerbosity.Info, "Init slave: " + client_name)
        client = WebsocketClient(request.sid, current_time())
        client.authenticated = True  # Need some authentication here
        APIController.slaves.add_slave(SlaveClient(APIController.next_id(), client_name, client))
        return client.authenticated

    @staticmethod
    @socketio.on('update', namespace="/Slave")
    def slave_update(topic, data):
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        if slave is None:
            Logger().write(LogVerbosity.Debug, "Slave update for not initialized slave")
            return

        Logger().write(LogVerbosity.Debug, "Slave update " + topic + ": " + data)

        slave_topic = str(slave.id) + "." + topic
        UIWebsocketController.broadcast(slave_topic, data)

    @staticmethod
    @socketio.on('notify', namespace="/Slave")
    def slave_request(topic, data):
        data = json.loads(data)
        Logger().write(LogVerbosity.Debug, "Slave notification " + topic + ": " + str(data))
        if topic == "update_watching_item":
            Database().update_watching_item(*data)

    @staticmethod
    @socketio.on('request', namespace="/Slave")
    def slave_request(request_id, topic, data):
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

    @staticmethod
    @socketio.on('ui_request', namespace="/Slave")
    def slave_ui_request(request_id, topic, data, timeout):
        Logger().write(LogVerbosity.Debug, "Slave ui request " + topic + ": " + data)
        slave = APIController.slaves.get_slave_by_sid(request.sid)
        UIWebsocketController.request_cb(topic, lambda *x: SlaveWebsocketController.slave_ui_request_callback(request_id, slave, x), timeout, json.loads(data))

    @staticmethod
    def slave_ui_request_callback(request_id, slave, response):
        Logger().write(LogVerbosity.Debug, "Slave ui request response id " + str(request_id) + ": " + str(response))
        socketio.emit("response", (request_id, *response), namespace="/Slave", room=slave._client.sid)

    @staticmethod
    def slave_command(slave_id, topic, command, args):
        slave = APIController.slaves.get_slave_by_id(slave_id)
        socketio.emit("command", (topic, command, args), namespace="/Slave", room=slave._client.sid)
