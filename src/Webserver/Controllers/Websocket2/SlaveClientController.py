from socketIO_client import SocketIO, BaseNamespace

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings


class SlaveClientController:

    socket = None
    slave_ns = None
    running = False

    @staticmethod
    def init():
        if Settings.get_int("log_level") == 0:
            import logging
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.basicConfig(level=logging.DEBUG)


    @staticmethod
    def connect():
        SlaveClientController.running = True
        Logger().write(LogVerbosity.Debug, "Connecting to master")
        SlaveClientController.socket = SocketIO(Settings.get_string("master_ip"), port=int(Settings.get_string("api_port")))
        SlaveClientController.slave_ns = SlaveClientController.socket.define(Handler, "/Slave")

        while SlaveClientController.running:
            SlaveClientController.socket.wait(1)

    def stop(self):
        SlaveClientController.running = False


class Handler(BaseNamespace):

    def on_connect(self, *args):
        Logger().write(LogVerbosity.Info, "Connected to master")

    def on_disconnect(self, *args):
        Logger().write(LogVerbosity.Info, "Disconnected from master")

    def on_event(self, test, *args):
        Logger().write(LogVerbosity.Info, "Received test event!")