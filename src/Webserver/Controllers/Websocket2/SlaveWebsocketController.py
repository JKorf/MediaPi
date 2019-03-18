from flask import request
from flask_socketio import emit

from Shared.Logger import Logger, LogVerbosity
from Shared.Util import current_time
from Webserver.APIController import socketio, WebsocketClient


class SlaveWebsocketController:
    clients = []
    last_data = dict()
    requests = []

    @staticmethod
    def init():
        pass

    @staticmethod
    @socketio.on('connect', namespace="/Slave")
    def connected():
        SlaveWebsocketController.clients.append(WebsocketClient(request.sid, current_time()))
        Logger().write(LogVerbosity.Info, "Slave client connected")

    @staticmethod
    @socketio.on('disconnect', namespace="/Slave")
    def disconnected():
        client = [x for x in SlaveWebsocketController.clients if x.sid == request.sid][0]
        SlaveWebsocketController.clients.remove(client)
        Logger().write(LogVerbosity.Info, "Slave client disconnected")

    @staticmethod
    @socketio.on('init', namespace="/Slave")
    def init_client(client_name):
        Logger().write(LogVerbosity.Info, "Init slave: " + client_name)
        client = [x for x in SlaveWebsocketController.clients if x.sid == request.sid][0]
        client.authenticated = True  # Need some authentication here
        return client.authenticated
