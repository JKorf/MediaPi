import asyncio

import tornado
from tornado import ioloop, web, websocket
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from Shared.Logger import Logger, LogVerbosity
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Webserver.Controllers.AuthController import AuthController
from Webserver.Controllers.DataController import DataController
from Webserver.Controllers.LightController import LightController
from Webserver.Controllers.MediaPlayer.HDController import HDController
from Webserver.Controllers.MediaPlayer.MovieController import MovieController
from Webserver.Controllers.MediaPlayer.PlayController import PlayController
from Webserver.Controllers.MediaPlayer.RadioController import RadioController
from Webserver.Controllers.MediaPlayer.ShowController import ShowController
from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController
from Webserver.Controllers.ToonController import ToonController
from Webserver.Controllers.UtilController import UtilController
from Webserver.Controllers.Websocket.MasterWebsocketController import MasterWebsocketController
from Webserver.Controllers.Websocket.SlaveWebsocketController import SlaveWebsocketController


class TornadoServer:
    master_ip = None

    def __init__(self):
        self.port = Settings.get_int("api_port")
        TornadoServer.master_ip = Settings.get_string("master_ip")
        if not Settings.get_bool("slave"):
            handlers = [
                (r"/auth/(.*)", AuthController),
                (r"/play/(.*)", PlayController),
                (r"/util/(.*)", UtilController),
                (r"/movies/(.*)", MovieController),
                (r"/shows/(.*)", ShowController),
                (r"/hd/(.*)", HDController),
                (r"/radio/(.*)", RadioController),
                (r"/torrent/(.*)", TorrentController),
                (r"/data/(.*)", DataController),
                (r"/toon/(.*)", ToonController),
                (r"/lighting/(.*)", LightController),
                (r"/ws", MasterWebsocketHandler)
            ]

            self.application = web.Application(handlers)
        else:
            self.slave_socket_controller = None

    def start(self):
        thread = CustomThread(self.internal_start, "Tornado server", [])
        thread.start()

    def internal_start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        if Settings.get_bool("slave"):
            self.slave_socket_controller = SlaveWebsocketController()
            self.slave_socket_controller.start()
            return

        MasterWebsocketController().start()

        self.application.listen(self.port)
        Logger().write(LogVerbosity.Info, "API running on port " + str(self.port))

        tornado.ioloop.IOLoop.instance().start()

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()


class MasterWebsocketHandler(websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):
        MasterWebsocketController().opening_client(self)

    def on_message(self, message):
        MasterWebsocketController().client_message(self, message)

    def on_close(self):
        MasterWebsocketController().closing_client(self)
