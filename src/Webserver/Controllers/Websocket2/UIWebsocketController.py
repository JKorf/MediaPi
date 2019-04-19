from flask import request
from flask_socketio import join_room, leave_room, emit

from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time, to_JSON
from Webserver.APIController import socketio, APIController, WebsocketClient, Request
from Webserver.Controllers.Websocket2.BaseWebsocketController import BaseWebsocketController


class UIWebsocketController(BaseWebsocketController):
    clients = []

    @staticmethod
    def init():
        from Controllers.TradfriManager import TradfriManager
        from MediaPlayer.MediaManager import MediaManager
        from MediaPlayer.Player.VLCPlayer import VLCPlayer
        from Updater import Updater
        from Shared.State import StateManager
        from Shared.Stats import Stats

        APIController.slaves.register_callback(lambda old, new: UIWebsocketController.broadcast("slaves", new.data))
        TradfriManager().tradfri_state.register_callback(lambda old, new: UIWebsocketController.broadcast("tradfri", new))
        StateManager().state_data.register_callback(lambda old, new: UIWebsocketController.broadcast("1.state", new))
        VLCPlayer().player_state.register_callback(lambda old, new: UIWebsocketController.broadcast("1.player", new))
        MediaManager().media_data.register_callback(lambda old, new: UIWebsocketController.broadcast("1.media", new))
        MediaManager().torrent_data.register_callback(lambda old, new: UIWebsocketController.broadcast("1.torrent", new))
        Stats().cache.register_callback(lambda old, new: UIWebsocketController.broadcast("1.stats", new))
        Updater().update_state.register_callback(lambda old, new: UIWebsocketController.broadcast("1.update", new))

    @staticmethod
    def on_connect():
        UIWebsocketController.clients.append(WebsocketClient(request.sid, current_time()))
        Logger().write(LogVerbosity.Info, "UI client connected")

    @staticmethod
    def on_disconnect():
        client = [x for x in UIWebsocketController.clients if x.sid == request.sid][0]
        UIWebsocketController.clients.remove(client)
        Logger().write(LogVerbosity.Info, "UI client disconnected")

    @staticmethod
    def on_init(client_id, session_key):
        Logger().write(LogVerbosity.Info, "Init UI: " + client_id + ", " + session_key)
        client = [x for x in UIWebsocketController.clients if x.sid == request.sid][0]

        client_key = APIController.get_salted(client_id)
        client.authenticated = Database().check_session_key(client_key, session_key)

        return client.authenticated

    @staticmethod
    def on_get_current_requests():
        for client_request in APIController().ui_websocket_controller.requests:
            socketio.emit("request", (client_request.request_id, client_request.topic, client_request.data), namespace="/UI", room=request.sid)

    @staticmethod
    def on_subscribe(topic):
        Logger().write(LogVerbosity.Info, "UI client subscribing to " + topic)
        join_room(topic)
        if topic in APIController.last_data:
            emit("update", (topic, to_JSON(APIController.last_data[topic])), namespace="/UI", room=request.sid)

    @staticmethod
    def on_unsubscribe(topic):
        Logger().write(LogVerbosity.Info, "UI client unsubscribing from " + topic)
        leave_room(topic)

    @staticmethod
    def broadcast(topic, data):
        APIController.last_data[topic] = data
        Logger().write(LogVerbosity.All, "Sending update: " + topic)
        socketio.emit("update", (topic, to_JSON(data)), namespace="/UI", room=topic)
