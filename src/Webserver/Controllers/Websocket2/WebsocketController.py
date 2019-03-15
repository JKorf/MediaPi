from threading import Event

import time
from flask import request
from flask_socketio import join_room, leave_room, emit

from Database.Database import Database
from Shared.Logger import LogVerbosity, Logger
from Shared.Threading import CustomThread
from Shared.Util import current_time, to_JSON
from Webserver.APIController import socketio, APIController


class WebsocketController:
    clients = []
    last_data = dict()
    requests = []

    @staticmethod
    def init():
        from Controllers.LightManager import LightManager
        from MediaPlayer.MediaManager import MediaManager
        from MediaPlayer.Player.VLCPlayer import VLCPlayer
        from Updater import Updater
        from Shared.State import StateManager
        from Shared.Stats import Stats

        APIController.slaves.register_callback(lambda old, new: WebsocketController.broadcast("slaves", new.data))
        LightManager().light_state.register_callback(lambda old, new: WebsocketController.broadcast("lights", new))
        StateManager().state_data.register_callback(lambda old, new: WebsocketController.broadcast("1.state", new))
        VLCPlayer().player_state.register_callback(lambda old, new: WebsocketController.broadcast("1.player", new))
        MediaManager().media_data.register_callback(lambda old, new: WebsocketController.broadcast("1.media", new))
        MediaManager().torrent_data.register_callback(lambda old, new: WebsocketController.broadcast("1.torrent", new))
        Stats().cache.register_callback(lambda old, new: WebsocketController.broadcast("1.stats", new))
        Updater().update_state.register_callback(lambda old, new: WebsocketController.broadcast("1.update", new))

        # t = CustomThread(WebsocketController.test, "test", [])
        # t.start()

    @staticmethod
    def test():
        time.sleep(3)
        start = current_time()
        request = WebsocketController.request("Test", [])
        response = request.wait(10)
        t = current_time() - start
        Logger().write(LogVerbosity.Debug, "Test 1 completed in " + str(t) + "ms, data: " + str(response))

        start = current_time()
        request = WebsocketController.request("Test2", [])
        response = request.wait(10)
        t = current_time() - start
        Logger().write(LogVerbosity.Debug, "Test 2 completed in " + str(t) + "ms, data: " + str(response))

        WebsocketController.request_cb("Test3", WebsocketController.test_result, 10, [])

    @staticmethod
    def test_result(response):
        Logger().write(LogVerbosity.Debug, "Test 3 completed, data: " + str(response))

    @staticmethod
    @socketio.on('connect', namespace="/UI")
    def connected():
        WebsocketController.clients.append(UIClient(request.sid, current_time()))
        Logger().write(LogVerbosity.Info, "UI client connected")

    @staticmethod
    @socketio.on('disconnect', namespace="/UI")
    def disconnected():
        client = [x for x in WebsocketController.clients if x.sid == request.sid][0]
        WebsocketController.clients.remove(client)
        Logger().write(LogVerbosity.Info, "UI client disconnected")

    @staticmethod
    @socketio.on('init', namespace="/UI")
    def init_client(client_id, session_key):
        Logger().write(LogVerbosity.Info, "Init: " + client_id + ", " + session_key)
        client = [x for x in WebsocketController.clients if x.sid == request.sid][0]

        client_key = APIController.get_salted(client_id)
        client.authenticated = Database().check_session_key(client_key, session_key)

        return client.authenticated

    @staticmethod
    @socketio.on('get_current_requests', namespace="/UI")
    def get_current_requests():
        for client_request in WebsocketController.requests:
            socketio.emit("request", (client_request.request_id, client_request.topic, client_request.data), namespace="/UI", room=request.sid)

    @staticmethod
    @socketio.on('subscribe', namespace="/UI")
    def subscribe(topic):
        Logger().write(LogVerbosity.Info, "UI client subscribing to " + topic)
        join_room(topic)
        if topic in WebsocketController.last_data:
            emit("update", (topic, WebsocketController.last_data[topic]), namespace="/UI", room=request.sid)

    @staticmethod
    @socketio.on('unsubscribe', namespace="/UI")
    def unsubscribe(topic):
        Logger().write(LogVerbosity.Info, "UI client unsubscribing from " + topic)
        leave_room(topic)

    @staticmethod
    @socketio.on('response', namespace="/UI")
    def response(request_id, args):
        Logger().write(LogVerbosity.Debug, "UI client response for id " + str(request_id) + ": " + str(args))
        requests = [x for x in WebsocketController.requests if x.request_id == request_id]
        if len(requests) == 0:
            Logger().write(LogVerbosity.Debug, "No pending request found for id " + str(request_id))
            return

        requests[0].set(args)

    @staticmethod
    def broadcast(topic, data):
        data = to_JSON(data)
        WebsocketController.last_data[topic] = data
        Logger().write(LogVerbosity.All, "Sending update: " + topic)
        socketio.emit("update", (topic, data), namespace="/UI", room=topic)

    @staticmethod
    def request(topic, *args):
        data = to_JSON(args)
        return WebsocketController._send_request(topic, data)

    @staticmethod
    def request_cb(topic, callback, timeout, *args):
        data = to_JSON(args)
        request = WebsocketController._send_request(topic, data)
        thread = CustomThread(WebsocketController.wait_for_request_response, "Request callback " + topic, [request, timeout, callback])
        thread.start()

    @staticmethod
    def wait_for_request_response(request, timeout, callback=None):
        response = request.wait(timeout)
        if callback is not None:
            if isinstance(response, list):
                callback(*response)
            else:
                callback(response)
        return response

    @staticmethod
    def _send_request(topic, data):
        Logger().write(LogVerbosity.Debug, "Sending request: " + topic +", data: " + str(data))
        request_id = APIController().next_id()
        request = Request(request_id, topic, data, WebsocketController._complete_request)
        WebsocketController.requests.append(request)
        socketio.emit("request", (request_id, topic, data), namespace="/UI")
        return request

    @staticmethod
    def _complete_request(request):
        WebsocketController.requests.remove(request)
        Logger().write(LogVerbosity.Debug, "Request done, now " + str(len(WebsocketController.requests)) + " requests open")


class Request:

    def __init__(self, request_id, topic, data, on_complete):
        self.evnt = Event()
        self.request_id = request_id
        self.topic = topic
        self.data = data
        self.response = None
        self.on_complete = on_complete

    def wait(self, timeout):
        if not self.evnt.wait(timeout):
            self.on_complete(self)
        return self.response

    def set(self, data):
        self.response = data
        self.on_complete(self)
        self.evnt.set()


class UIClient:

    def __init__(self, sid, connect_time):
        self.sid = sid
        self.connect_time = connect_time
        self.authenticated = False


