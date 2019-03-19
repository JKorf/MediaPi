from socketIO_client import SocketIO, BaseNamespace

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import to_JSON
from Webserver.APIController import APIController, Request


class SlaveClientController:

    socket = None
    slave_ns = None
    running = False
    requests = []
    last_data = dict()

    @staticmethod
    def init():
        if Settings.get_int("log_level") == 0:
            import logging
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.basicConfig(level=logging.DEBUG)

        from MediaPlayer.MediaManager import MediaManager
        from MediaPlayer.Player.VLCPlayer import VLCPlayer
        from Updater import Updater
        from Shared.State import StateManager
        from Shared.Stats import Stats

        StateManager().state_data.register_callback(lambda old, new: SlaveClientController.broadcast("state", new))
        VLCPlayer().player_state.register_callback(lambda old, new: SlaveClientController.broadcast("player", new))
        MediaManager().media_data.register_callback(lambda old, new: SlaveClientController.broadcast("media", new))
        MediaManager().torrent_data.register_callback(lambda old, new: SlaveClientController.broadcast("torrent", new))
        Stats().cache.register_callback(lambda old, new: SlaveClientController.broadcast("stats", new))
        Updater().update_state.register_callback(lambda old, new: SlaveClientController.broadcast("update", new))

    @staticmethod
    def connect():
        SlaveClientController.running = True
        Logger().write(LogVerbosity.Debug, "Connecting to master")
        SlaveClientController.socket = SocketIO(Settings.get_string("master_ip"), port=int(Settings.get_string("api_port")))
        SlaveClientController.slave_ns = SlaveClientController.socket.define(Handler, "/Slave")

        while SlaveClientController.running:
            SlaveClientController.socket.wait(1)

    @staticmethod
    def broadcast(topic, data):
        if not isinstance(data, str):
            data = to_JSON(data)
        SlaveClientController.last_data[topic] = data
        if SlaveClientController.slave_ns is not None:
            SlaveClientController.slave_ns.emit("update", topic, data)

    @staticmethod
    def request_ui_cb(topic, callback, timeout, *args):
        data = to_JSON(args)
        request = SlaveClientController._send_ui_request(topic, data, timeout)
        thread = CustomThread(SlaveClientController.wait_for_request_response, "Request callback " + topic, [request, timeout, callback])
        thread.start()

    @staticmethod
    def request_master(topic, timeout, *args):
        data = to_JSON(args)
        request = SlaveClientController._send_request(topic, data)
        return request.wait(timeout)

    @staticmethod
    def wait_for_request_response(request, timeout, callback=None):
        response = request.wait(timeout)
        if callback is not None:
            callback(*response)
        return response

    @staticmethod
    def on_response(request_id, response):
        Logger().write(LogVerbosity.Debug, "UI client response for id " + str(request_id) + ": " + str(response))
        requests = [x for x in SlaveClientController.requests if x.request_id == request_id]
        if len(requests) == 0:
            Logger().write(LogVerbosity.Debug, "No pending request found for id " + str(request_id))
            return

        requests[0].set(response)

    @staticmethod
    def on_command(topic, command, args):
        Logger().write(LogVerbosity.Debug, "Master command " + topic + ": " + command)

        method = None
        if topic == "media":
            from MediaPlayer.MediaManager import MediaManager
            method = getattr(MediaManager(), command)

        if method is not None:
            cb_thread = CustomThread(method, "Master command", args)
            cb_thread.start()

    @staticmethod
    def _send_request(topic, data):
        Logger().write(LogVerbosity.Debug, "Sending request: " + topic + ", data: " + str(data))
        request_id = APIController().next_id()
        request = Request(request_id, topic, data, SlaveClientController._complete_request)
        SlaveClientController.requests.append(request)
        SlaveClientController.slave_ns.emit("request", request_id, topic, data)
        return request

    @staticmethod
    def _send_ui_request(topic, data, timeout):
        Logger().write(LogVerbosity.Debug, "Sending ui request: " + topic + ", data: " + str(data))
        request_id = APIController().next_id()
        request = Request(request_id, topic, data, SlaveClientController._complete_request)
        SlaveClientController.requests.append(request)
        SlaveClientController.slave_ns.emit("ui_request", request_id, topic, data, timeout)
        return request

    @staticmethod
    def _complete_request(request):
        SlaveClientController.requests.remove(request)
        Logger().write(LogVerbosity.Debug, "Request done, now " + str(len(SlaveClientController.requests)) + " requests open")

    @staticmethod
    def stop():
        SlaveClientController.running = False


class Handler(BaseNamespace):

    def on_connect(self, *args):
        self.initialize()

    def on_reconnect(self, *args):
        self.initialize()

    def initialize(self):
        Logger().write(LogVerbosity.Info, "Connected to master")
        self.emit("init", Settings.get_string("name"))
        for k, v in SlaveClientController.last_data.items():
            SlaveClientController.broadcast(k, v)

    def on_response(self, request_id, *args):
        SlaveClientController.on_response(request_id, args)

    def on_command(self, *args):
        SlaveClientController.on_command(*args)

    def on_disconnect(self, *args):
        Logger().write(LogVerbosity.Info, "Disconnected from master")
