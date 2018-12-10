import asyncio
import os
import traceback
import urllib.parse
import urllib.request

import tornado
from Webserver.Controllers.HDController import HDController
from Webserver.Controllers.LightController import LightController
from Webserver.Controllers.MovieController import MovieController
from Webserver.Controllers.PlayerController import PlayerController
from Webserver.Controllers.RadioController import RadioController
from Webserver.Controllers.TorrentController import TorrentController
from Webserver.Controllers.UtilController import UtilController
from Webserver.Controllers.WebsocketController import WebsocketController
from Webserver.Controllers.YoutubeController import YoutubeController
from tornado import ioloop, web, websocket
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from Controllers.TVController import TVManager
from Database.Database import Database
from MediaPlayer.MediaManager import MediaManager
from MediaPlayer.Util.Enums import TorrentState
from MediaPlayer.Util.Util import get_file_info
from Webserver.Controllers.ShowController import ShowController
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import to_JSON


class TornadoServer:
    master_ip = None
    clients = []

    def __init__(self):
        self.port = 80
        TornadoServer.master_ip = Settings.get_string("master_ip")
        handlers = [
            (r"/util/(.*)", UtilHandler),
            (r"/movies/(.*)", MovieHandler),
            (r"/shows/(.*)", ShowHandler),
            (r"/hd/(.*)", HDHandler),
            (r"/player/(.*)", PlayerHandler),
            (r"/radio/(.*)", RadioHandler),
            (r"/youtube/(.*)", YoutubeHandler),
            (r"/torrent/(.*)", TorrentHandler),
            (r"/lighting/(.*)", LightHandler),
            (r"/tv/(.*)", TVHandler),
            (r"/realtime", RealtimeHandler),
            (r"/database/(.*)", DatabaseHandler),
            (r"/(.*)", StaticFileHandler, {"path": os.getcwd() + "/UI/WebNew", "default_filename": "index.html"})
        ]

        self.application = web.Application(handlers)

    def start(self):
        thread = CustomThread(self.internal_start, "Tornado server", [])
        thread.start()

    def internal_start(self):
        WebsocketController.init()
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
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


class BaseHandler(tornado.web.RequestHandler):
    def _handle_request_exception(self, e):
        Logger.write(3, "Error in Tornado requests: " + str(e), 'error')
        stack_trace = traceback.format_exc().split('\n')
        for stack_line in stack_trace:
            Logger.write(3, stack_line)


class UtilHandler(BaseHandler):
    async def get(self, url):
        if url == "get_protected_img":
            data = await UtilController.get_protected_img(self.get_argument("url"))
            self.write(data)
        elif url == "startup":
            self.write(UtilController.startup())
        elif url == "info":
            self.write(UtilController.info())
        elif url == "get_subtitles":
            data = MediaManager().subtitle_provider.search_subtitles_for_file(self.get_argument("path"), self.get_argument("file"))
            self.write(to_JSON(data))

    def post(self, url):
        if url == "shutdown":
            UtilController.shutdown()
        elif url == "restart_pi":
            UtilController.restart_pi()
        elif url == "test":
            UtilController.test()


class MovieHandler(BaseHandler):
    def post(self, url):
        if url == "play_movie":
            MovieController.play_movie(self.get_argument("url"), self.get_argument("id"), self.get_argument("title"), self.get_argument("img", ""))
        elif url == "play_continue":
            MovieController.play_continue(TornadoServer, HDController.play_master_file, self.get_argument("type"), self.get_argument("url"), self.get_argument("title"), self.get_argument("image"), self.get_argument("position"), self.get_argument("mediaFile"))

    async def get(self, url):
        if url == "get_movies":
            data = await MovieController.get_movies(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_movies_all":
            data = await MovieController.get_movies_all(self.get_argument("page"), self.get_argument("orderby"),
                                                     self.get_argument("keywords"))
            self.write(data)
        elif url == "get_movie":
            data = await MovieController.get_movie(self.get_argument("id"))
            self.write(data)


class ShowHandler(BaseHandler):

    def post(self, url):
        if url == "play_episode":
            ShowController.play_episode(self.get_argument("url"), self.get_argument("id"), self.get_argument("title"), self.get_argument("img", ""), self.get_argument("season"), self.get_argument("episode"))

    async def get(self, url):
        if url == "get_shows":
            data = await ShowController.get_shows(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_shows_all":
            data = await ShowController.get_shows_all(self.get_argument("page"), self.get_argument("orderby"),
                                                   self.get_argument("keywords"))
            self.write(data)
        elif url == "get_show":
            show = await ShowController.get_show(self.get_argument("id"))
            self.write(show)


class RadioHandler(BaseHandler):
    def get(self, url):
        if url == "get_radios":
            self.write(RadioController.get_radios())

    def post(self, url):
        if url == "play_radio":
            RadioController.play_radio(self.get_argument("id"))


class PlayerHandler(BaseHandler):
    def post(self, url):
        if url == "set_subtitle_file":
            PlayerController.set_subtitle_file(self.get_argument("file"))
        elif url == "set_subtitle_id":
            PlayerController.set_subtitle_id(self.get_argument("sub"))
        elif url == "stop_player":
            was_waiting_for_file_selection = MediaManager().torrent and MediaManager().torrent.state == TorrentState.WaitingUserFileSelection
            PlayerController.stop_player()

            if was_waiting_for_file_selection:
                WebsocketController.broadcast('request', 'media_selection_close', [])

        elif url == "pause_resume_player":
            PlayerController.pause_resume_player()
        elif url == "change_volume":
            PlayerController.change_volume(self.get_argument("vol"))
        elif url == "change_subtitle_offset":
            PlayerController.change_subtitle_offset(self.get_argument("offset"))
        elif url == "seek":
            PlayerController.seek(self.get_argument("pos"))
        elif url == "set_audio_id":
            PlayerController.set_audio_track(self.get_argument("track"))
        elif url == "select_file":
            EventManager.throw_event(EventType.TorrentMediaFileSelection, [urllib.parse.unquote(self.get_argument("path"))])


class HDHandler(BaseHandler):
    async def get(self, url):
        if Settings.get_bool("slave"):
            self.write(await TornadoServer.request_master_async(self.request.uri))
        elif url == "drives":
            self.write(HDController.drives())
        elif url == "directory":
            self.write(HDController.directory(self.get_argument("path")))

    async def post(self, url):
        if url == "play_file":
            if Settings.get_bool("slave"):
                Logger.write(2, self.get_argument("path"))
                await HDController.play_master_file(TornadoServer, self.get_argument("path"), self.get_argument("filename"), 0)

            else:
                filename = self.get_argument("filename")
                HDController.play_file(filename, self.get_argument("path"))
                file = urllib.parse.unquote(self.get_argument("path"))
                if not filename.endswith(".jpg"):
                    size, first_64k, last_64k = get_file_info(file)
                    EventManager.throw_event(EventType.HashDataKnown, [size, file, first_64k, last_64k])

        elif url == "next_image":
            HDController.next_image(self.get_argument("current_path"))
        elif url == "prev_image":
            HDController.prev_image(self.get_argument("current_path"))


class YoutubeHandler(BaseHandler):
    async def get(self, url):
        if url == "search":
            data = await YoutubeController.search(self.get_argument("query"), self.get_argument("type"))
            self.write(data)
        elif url == "home":
            data = await YoutubeController.home()
            self.write(data)
        elif url == "channel_info":
            data = await YoutubeController.channel_info(self.get_argument("id"))
            self.write(data)
        elif url == "channel_feed":
            data = await YoutubeController.channel_feed(self.get_argument("id"))
            self.write(data)

    def post(self, url):
        if url == "play_youtube":
            YoutubeController.play_youtube(self.get_argument("id"), self.get_argument("title"))
        elif url == "play_youtube_url":
            YoutubeController.play_youtube_url(self.get_argument("url"), self.get_argument("title"))


class TorrentHandler(BaseHandler):
    def get(self, url):
        if url == "top":
            self.write(TorrentController.top())
        elif url == "search":
            self.write(TorrentController.search(self.get_argument("keywords")))

    def post(self, url):
        if url == "play_torrent":
            TorrentController.play_torrent(self.get_argument("url"), self.get_argument("title"))


class LightHandler(BaseHandler):
    def get(self, url):
        if url == "get_lights":
            self.write(LightController.get_lights())

    def post(self, url):
        if url == "switch_light":
            LightController.switch_light(int(self.get_argument("index")), self.get_argument("state") == "on")
        elif url == "warmth_light":
            LightController.warmth_light(int(self.get_argument("index")), int(self.get_argument("warmth")))
        elif url == "dimmer_light":
            LightController.dimmer_light(int(self.get_argument("index")), int(self.get_argument("dimmer")))


class TVHandler(BaseHandler):
    def get(self, url):
        if url == "get_devices":
            self.write(to_JSON(TVManager().get_inputs()))

    def post(self, url):
        if url == "tv_on":
            TVManager().turn_tv_on()
        elif url == "tv_off":
            TVManager().turn_tv_off()
        elif url == "channel_up":
            TVManager().channel_up()
        elif url == "channel_down":
            TVManager().channel_down()


class RealtimeHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        WebsocketController.opening_client(self)

    def on_close(self):
        WebsocketController.closing_client(self)


class DatabaseHandler(BaseHandler):
    async def get(self, url):
        if Settings.get_bool("slave"):
            self.write(await TornadoServer.request_master_async(self.request.uri))
            return

        if url == "get_favorites":
            Logger.write(2, "Getting favorites")
            self.write(to_JSON(Database().get_favorites()))

        if url == "get_history":
            Logger.write(2, "Getting history")
            self.write(to_JSON(Database().get_history()))

        if url == "get_unfinished_items":
            Logger.write(2, "Getting unfinished items")
            self.write(to_JSON(Database().get_watching_items()))

    async def post(self, url):
        if Settings.get_bool("slave"):
            await TornadoServer.notify_master_async(self.request.uri)
            return

        if url == "add_watched_torrent_file":
            Logger.write(2, "Adding to watched torrent files")
            Database().add_watched_torrent_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("mediaFile"), self.get_argument("watchedAt"))

        if url == "add_watched_file":
            Logger.write(2, "Adding to watched files")
            Database().add_watched_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("watchedAt"), urllib.parse.unquote(self.get_argument("mediaFile")))

        if url == "add_watched_youtube":
            Logger.write(2, "Adding to watched youtube")
            Database().add_watched_youtube(
                self.get_argument("title"),
                self.get_argument("watchedAt"),
                self.get_argument("id"),
                self.get_argument("url"))

        if url == "add_watched_movie":
            Logger.write(2, "Adding to watched movie")
            Database().add_watched_movie(
                self.get_argument("title"),
                self.get_argument("movieId"),
                self.get_argument("image"),
                self.get_argument("watchedAt"),
                self.get_argument("url"),
                self.get_argument("mediaFile"))

        if url == "add_watched_episode":
            Logger.write(2, "Adding to watched episodes")
            Database().add_watched_episode(
                self.get_argument("title"),
                self.get_argument("showId"),
                self.get_argument("url"),
                self.get_argument("mediaFile"),
                self.get_argument("image"),
                self.get_argument("episodeSeason"),
                self.get_argument("episodeNumber"),
                self.get_argument("watchedAt"))

        if url == "add_watched_torrent":
            Logger.write(2, "Adding to watched episodes")
            Database().add_watched_torrent_file(
                self.get_argument("title"),
                self.get_argument("url"),
                self.get_argument("mediaFile"),
                self.get_argument("watchedAt"))

        if url == "remove_watched":
            Logger.write(2, "Remove watched")
            Database().remove_watched(self.get_argument("id"))

        if url == "add_favorite":
            Logger.write(2, "Adding to favorites")
            Database().add_favorite(self.get_argument("id"), self.get_argument("type"), self.get_argument("title"), self.get_argument("image"))

        if url == "remove_favorite":
            Logger.write(2, "Removing from favorites")
            Database().remove_favorite(self.get_argument("id"))

        if url == "remove_unfinished":
            Logger.write(2, "Removing unfinished")
            Database().remove_watching_item(
                urllib.parse.unquote(self.get_argument("url")))

        if url == "add_unfinished":
            Logger.write(2, "Adding unfinished")

            media_file = self.get_argument("mediaFile")
            if media_file == "None" or media_file == "null":
                media_file = None
            Database().add_watching_item(
                self.get_argument("type"),
                self.get_argument("name"),
                urllib.parse.unquote(self.get_argument("url")),
                self.get_argument("image"),
                int(self.get_argument("length")),
                self.get_argument("time"),
                media_file)

        if url == "update_unfinished":
            media_file = self.get_argument("mediaFile")
            if media_file == "None" or media_file == "null":
                media_file = None

            Database().update_watching_item(
                urllib.parse.unquote(self.get_argument("url")),
                int(self.get_argument("position")),
                self.get_argument("watchedAt"),
                media_file)
