import time

from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from WebServer.TornadoServer import TornadoServer


class WebServerManager:

    def __init__(self, start):
        self.server = None
        self.start = start

    def start_server(self):
        self.server = TornadoServer(self.start)
        self.server.start()
        if Settings.get_bool("show_gui"):
            thread = CustomThread(self.set_address, "Set gui address")
            thread.start()

    def set_address(self):
        while not self.start.gui_manager.gui:
            time.sleep(1)

        actual_address = self.server.get_actual_address()
        Logger.write(3, "WebServer running on " + actual_address)
        self.start.gui_manager.gui.set_address(actual_address)
