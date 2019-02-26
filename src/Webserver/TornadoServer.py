import asyncio
import os
import urllib.parse
import urllib.request

import tornado
from tornado import ioloop, web, websocket
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings, SecureSettings
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
        Logger.write(2, "API running on port " + str(self.port))

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


# class DatabaseHandler(BaseHandler):
#
#     async def post(self, url):
#         if Settings.get_bool("slave"):
#             await TornadoServer.notify_master_async(self.request.uri)
#             return
#
#         if url == "add_watched_torrent_file":
#             Logger.write(2, "Adding to watched torrent files")
#             Database().add_watched_torrent_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("mediaFile"), self.get_argument("watchedAt"))
#
#         if url == "add_watched_file":
#             Logger.write(2, "Adding to watched files")
#             Database().add_watched_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("watchedAt"), urllib.parse.unquote(self.get_argument("mediaFile")))
#
#         if url == "add_watched_youtube":
#             Logger.write(2, "Adding to watched youtube")
#             Database().add_watched_youtube(
#                 self.get_argument("title"),
#                 self.get_argument("watchedAt"),
#                 self.get_argument("id"),
#                 self.get_argument("url"))
#
#         if url == "add_watched_movie":
#             Logger.write(2, "Adding to watched movie")
#             Database().add_watched_movie(
#                 self.get_argument("title"),
#                 self.get_argument("movieId"),
#                 self.get_argument("image"),
#                 self.get_argument("watchedAt"),
#                 self.get_argument("url"),
#                 self.get_argument("mediaFile"))
#
#         if url == "add_watched_episode":
#             Logger.write(2, "Adding to watched episodes")
#             Database().add_watched_episode(
#                 self.get_argument("title"),
#                 self.get_argument("showId"),
#                 self.get_argument("url"),
#                 self.get_argument("mediaFile"),
#                 self.get_argument("image"),
#                 self.get_argument("episodeSeason"),
#                 self.get_argument("episodeNumber"),
#                 self.get_argument("watchedAt"))
#
#         if url == "add_watched_torrent":
#             Logger.write(2, "Adding to watched episodes")
#             Database().add_watched_torrent_file(
#                 self.get_argument("title"),
#                 self.get_argument("url"),
#                 self.get_argument("mediaFile"),
#                 self.get_argument("watchedAt"))
#
#         if url == "remove_watched":
#             Logger.write(2, "Remove watched")
#             Database().remove_watched(self.get_argument("id"))
#
#         if url == "add_favorite":
#             Logger.write(2, "Adding to favorites")
#             Database().add_favorite(self.get_argument("id"), self.get_argument("type"), self.get_argument("title"), self.get_argument("image"))
#
#         if url == "remove_favorite":
#             Logger.write(2, "Removing from favorites")
#             Database().remove_favorite(self.get_argument("id"))
#
#         if url == "remove_unfinished":
#             Logger.write(2, "Removing unfinished")
#             Database().remove_watching_item(
#                 urllib.parse.unquote(self.get_argument("url")))
#
#         if url == "add_unfinished":
#             Logger.write(2, "Adding unfinished")
#
#             media_file = self.get_argument("mediaFile")
#             if media_file == "None" or media_file == "null":
#                 media_file = None
#             Database().add_watching_item(
#                 self.get_argument("type"),
#                 self.get_argument("name"),
#                 urllib.parse.unquote(self.get_argument("url")),
#                 self.get_argument("image"),
#                 int(self.get_argument("length")),
#                 self.get_argument("time"),
#                 media_file)
#
#         if url == "update_unfinished":
#             media_file = self.get_argument("mediaFile")
#             if media_file == "None" or media_file == "null":
#                 media_file = None
#
#             Database().update_watching_item(
#                 urllib.parse.unquote(self.get_argument("url")),
#                 int(self.get_argument("position")),
#                 self.get_argument("watchedAt"),
#                 media_file)
