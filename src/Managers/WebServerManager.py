import time

from Managers.GUIManager import GUIManager
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import Singleton
from WebServer.Controllers.WebsocketController import WebsocketController
from WebServer.TornadoServer import TornadoServer


class WebServerManager(metaclass=Singleton):

    def __init__(self):
        self.server = None

    def start_server(self):
        WebsocketController.init()

        self.server = TornadoServer()
        self.server.start()
        if Settings.get_bool("show_gui"):
            thread = CustomThread(self.set_address, "Set gui address")
            thread.start()

    def set_address(self):
        while not GUIManager().gui:
            time.sleep(1)

        actual_address = self.server.get_actual_address()
        Logger.write(3, "WebServer running on " + actual_address)
        GUIManager().gui.set_address(actual_address)
