import asyncio
import os
import urllib.parse
import urllib.request

import tornado
from tornado import ioloop, web, websocket
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from Database.Database import Database
from MediaPlayer.MediaPlayer import MediaManager
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import to_JSON
from Webserver.Controllers.DataController import DataController
from Webserver.Controllers.MediaPlayer.HDController import HDController
from Webserver.Controllers.MediaPlayer.MovieController import MovieController
from Webserver.Controllers.MediaPlayer.PlayController import PlayController
from Webserver.Controllers.MediaPlayer.RadioController import RadioController
from Webserver.Controllers.MediaPlayer.ShowController import ShowController
from Webserver.Controllers.MediaPlayer.TorrentController import TorrentController
from Webserver.Controllers.UtilController import UtilController
from Webserver.Controllers.Websocket.MasterWebsocketController import MasterWebsocketController
from Webserver.Controllers.Websocket.SlaveWebsocketController import SlaveWebsocketController
from Webserver.BaseHandler import BaseHandler


class TornadoServer:
    master_ip = None

    def __init__(self):
        self.port = 80
        TornadoServer.master_ip = Settings.get_string("master_ip")
        if not Settings.get_bool("slave"):
            handlers = [
                (r"/play/(.*)", PlayController),
                (r"/util/(.*)", UtilController),
                (r"/movies/(.*)", MovieController),
                (r"/shows/(.*)", ShowController),
                (r"/hd/(.*)", HDController),
                (r"/radio/(.*)", RadioController),
                (r"/torrent/(.*)", TorrentController),
                (r"/ws", MasterWebsocketHandler),
                (r"/data/(.*)", DataController),
                (r"/(.*)", StaticFileHandler, {"path": os.getcwd() + "/UI/homebase/build", "default_filename": "index.html"})
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

        while True:
            try:
                self.application.listen(self.port)
                Logger.write(2, "Tornado server running on port " + str(self.port))
                break
            except OSError:
                self.port += 1
        tornado.ioloop.IOLoop.instance().start()

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()

    @staticmethod
    async def notify_master_async(url):
        reroute = str(TornadoServer.master_ip) + url
        Logger.write(2, "Sending notification to master at " + reroute)
        await RequestFactory.make_request_async(reroute, "POST")

    @staticmethod
    def notify_master(url):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(TornadoServer.notify_master_async(url))

    @staticmethod
    def request_master(url):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(TornadoServer.request_master_async(url))

    @staticmethod
    async def request_master_async(url):
        reroute = str(TornadoServer.master_ip) + url
        Logger.write(2, "Sending request to master at " + reroute)
        return await RequestFactory.make_request_async(reroute, "GET")


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

        if path.endswith(".js"):
            self.set_header('content-type', 'application/javascript')
        if path.endswith(".css"):
            self.set_header('content-type', 'text/css')


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
