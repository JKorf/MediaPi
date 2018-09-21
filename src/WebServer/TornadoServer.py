import base64
import json
import os
import socket
import time
import urllib.parse
import urllib.request
from threading import Lock

import tornado
from tornado import gen
from tornado import ioloop, web, websocket

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Threading import CustomThread
from Shared.Util import to_JSON, RequestFactory
from MediaPlayer.Util.Enums import TorrentState
from MediaPlayer.Util.Util import get_file_info
from WebServer.Controllers.HDController import HDController
from WebServer.Controllers.MovieController import MovieController
from WebServer.Controllers.PlayerController import PlayerController
from WebServer.Controllers.RadioController import RadioController
from WebServer.Controllers.ShowController import ShowController
from WebServer.Controllers.TorrentController import TorrentController
from WebServer.Controllers.UtilController import UtilController
from WebServer.Controllers.YoutubeController import YoutubeController
from WebServer.Models import WebSocketMessage, MediaFile


class TornadoServer:
    start_obj = None
    master_ip = None
    clients = []
    _ws_lock = Lock()

    def __init__(self, start):
        self.port = 80
        TornadoServer.master_ip = Settings.get_string("master_ip")
        TornadoServer.start_obj = start
        handlers = [
            (r"/util/(.*)", UtilHandler),
            (r"/movies/(.*)", MovieHandler),
            (r"/shows/(.*)", ShowHandler),
            (r"/hd/(.*)", HDHandler),
            (r"/player/(.*)", PlayerHandler),
            (r"/radio/(.*)", RadioHandler),
            (r"/youtube/(.*)", YoutubeHandler),
            (r"/torrent/(.*)", TorrentHandler),
            (r"/realtime", RealtimeHandler),
            (r"/database/(.*)", DatabaseHandler),
            (r"/(.*)", StaticFileHandler, {"path": os.getcwd() + "/Interface/Mobile", "default_filename": "index.html"})
        ]

        self.application = web.Application(handlers)

        EventManager.register_event(EventType.NextEpisodeSelection, self.next_episode_selection)
        EventManager.register_event(EventType.TorrentMediaSelectionRequired, self.media_selection_required)
        EventManager.register_event(EventType.TorrentMediaFileSelection, self.media_selected)
        EventManager.register_event(EventType.PlayerStateChange, self.player_state_changed)
        EventManager.register_event(EventType.PlayerError, self.player_error)
        EventManager.register_event(EventType.Seek, self.player_seeking)
        EventManager.register_event(EventType.SetVolume, self.player_volume)
        EventManager.register_event(EventType.SetSubtitleId, self.player_subtitle_id)
        EventManager.register_event(EventType.SetSubtitleOffset, self.player_subtitle_offset)
        EventManager.register_event(EventType.Error, self.application_error)

    def start(self):
        while True:
            try:
                self.application.listen(self.port)
                Logger.write(2, "Tornado server running on port " + str(self.port))
                break
            except OSError:
                self.port += 1

        thread = CustomThread(self.internal_start, "Tornado server", [])
        thread.start()

    def internal_start(self):
        ioloop.IOLoop.instance().start()

    def stop(self):
        ioloop.IOLoop.instance().stop()

    def notify_master(self, url):
        reroute = str(TornadoServer.master_ip) + url
        Logger.write(2, "Sending notification to master at " + reroute)
        RequestFactory.make_request(reroute, "POST")

    def get_actual_address(self):
        for i in range(3):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("gmail.com", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip + ":" + str(self.port)

            except Exception as e:
                Logger.write(3, "Failed to connect to remote server, try " + str(i))
                time.sleep(10)
        return "No internet connection"

    def next_episode_selection(self, path, name, season, episode, type, media_file, img):
        self.broadcast("request", "next_episode", MediaFile(path, name, 0, season, episode, type, media_file, img, False))

    def media_selected(self, file):
        self.broadcast("request", "media_selection_close")

    def media_selection_required(self, files):
        if not Settings.get_bool("slave"):
            watched_files = [f[9] for f in TornadoServer.start_obj.database.get_watched_torrent_files(TornadoServer.start_obj.torrent_manager.torrent.uri)]
            files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in files]
        else:
            files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in files]
        self.broadcast("request", "media_selection", files)

    def player_state_changed(self, old_state, state):
        self.broadcast("player_event", "state_change", state.value)

    def player_error(self):
        self.broadcast("player_event", "error")

    def player_seeking(self, pos):
        self.broadcast("player_event", "seek", pos / 1000)

    def player_volume(self, vol):
        self.broadcast("player_event", "volume", vol)

    def player_subtitle_id(self, id):
        self.broadcast("player_event", "subtitle_id", id)

    def player_subs_done_change(self, done):
        self.broadcast("player_event", "subs_done_change", done)

    def player_subtitle_offset(self, offset):
        self.broadcast("player_event", "subtitle_offset", float(offset) / 1000 / 1000)

    def application_error(self, error_type, error_message):
        self.broadcast("error_event", error_type, error_message)

    @staticmethod
    def broadcast(event, method, parameters=None):
        if parameters is None:
            parameters = ""

        with TornadoServer._ws_lock:
            for client in TornadoServer.clients:
                client.write_message(to_JSON(WebSocketMessage(event, method, parameters)))


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Disable cache
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')


class UtilHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "player_state":
            self.write(UtilController.player_state(TornadoServer.start_obj))
        elif url == "get_protected_img":
            data = yield UtilController.get_protected_img(self.get_argument("url"))
            self.write(data)
        elif url == "media_info":
            self.write(UtilController.media_info(TornadoServer.start_obj))
        elif url == "startup":
            self.write(UtilController.startup())
        elif url == "info":
            self.write(UtilController.info())
        elif url == "get_settings":
            self.write(UtilController.get_settings())
        elif url == "version":
            self.write(UtilController.version(TornadoServer.start_obj))
        elif url == "status":
            self.write(UtilController.status(TornadoServer.start_obj))

    @gen.coroutine
    def post(self, url):
        if url == "save_settings":
            UtilController.save_settings(self.get_argument("raspberry"), self.get_argument("gui"), self.get_argument("external_trackers"), self.get_argument("max_subs"))
        elif url == "shutdown":
            UtilController.shutdown()
        elif url == "restart_pi":
            UtilController.restart_pi()
        elif url == "test":
            UtilController.test()


class MovieHandler(web.RequestHandler):
    @gen.coroutine
    def post(self, url):
        if url == "play_movie":
            MovieController.play_movie(self.get_argument("url"), self.get_argument("id"), self.get_argument("title"), self.get_argument("img", ""))
        elif url == "play_continue":
            yield MovieController.play_continue(play_master_file, self.get_argument("type"), self.get_argument("url"), self.get_argument("title"), self.get_argument("image"), self.get_argument("position"), self.get_argument("mediaFile"))

    @gen.coroutine
    def get(self, url):
        if url == "get_movies":
            data = yield MovieController.get_movies(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_movies_all":
            data = yield MovieController.get_movies_all(self.get_argument("page"), self.get_argument("orderby"),
                                                     self.get_argument("keywords"))
            self.write(data)
        elif url == "get_movie":
            data = yield MovieController.get_movie(self.get_argument("id"))
            self.write(data)


class ShowHandler(web.RequestHandler):

    def post(self, url):
        if url == "play_episode":
            ShowController.play_episode(self.get_argument("url"), self.get_argument("title"), self.get_argument("img", ""))

    @gen.coroutine
    def get(self, url):
        if url == "get_shows":
            data = yield ShowController.get_shows(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_shows_all":
            data = yield ShowController.get_shows_all(self.get_argument("page"), self.get_argument("orderby"),
                                                   self.get_argument("keywords"))
            self.write(data)
        elif url == "get_show":
            show = yield ShowController.get_show(self.get_argument("id"))
            self.write(show)


class RadioHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "get_radios":
            self.write(RadioController.get_radios())

    def post(self, url):
        if url == "play_radio":
            RadioController.play_radio(self.get_argument("id"))


class PlayerHandler(web.RequestHandler):
    def post(self, url):
        if url == "set_subtitle_file":
            PlayerController.set_subtitle_file(self.get_argument("file"))
        elif url == "set_subtitle_id":
            PlayerController.set_subtitle_id(self.get_argument("sub"))
        elif url == "stop_player":
            was_waiting_for_file_selection = TornadoServer.start_obj.torrent_manager.torrent and TornadoServer.start_obj.torrent_manager.torrent.state == TorrentState.WaitingUserFileSelection
            PlayerController.stop_player()

            if was_waiting_for_file_selection:
                TornadoServer.broadcast('request', 'media_selection_close', [])

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


class HDHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if Settings.get_bool("slave"):
            yield self.reroute_to_master()
        elif url == "drives":
            self.write(HDController.drives())
        elif url == "get_hash_data": # TODO need to do this different
            file = self.get_argument("path")
            size, first, last = get_file_info(file)
            first_base = base64.b64encode(first)
            last_base = base64.b64encode(last)
            obj = {
                "file": file,
                "size": size,
                "first": str(first_base),
                "last": str(last_base)
            }

            self.write(json.dumps(obj))
        elif url == "directory":
            self.write(HDController.directory(self.get_argument("path")))

    @gen.coroutine
    def post(self, url):
        if url == "play_file":
            if Settings.get_bool("slave"):
                Logger.write(2, self.get_argument("path"))
                play_master_file(self.get_argument("path"), self.get_argument("filename"), 0)

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

    @gen.coroutine
    def reroute_to_master(self):
        reroute = str(TornadoServer.master_ip) + self.request.uri
        Logger.write(2, "Sending request to master at " + reroute)
        result = yield RequestFactory.make_request_async(reroute, self.request.method)
        if result:
            self.write(result)

@gen.coroutine
def play_master_file(path, file, position):
    # play file from master
    file_location = TornadoServer.master_ip + ":50010/file"
    if not path.startswith("/"):
        file_location += "/"
    HDController.play_file(file,
                           file_location + urllib.parse.quote_plus(path),
                           position)

    # request hash from master
    json_data = yield RequestFactory.make_request_async(
        Settings.get_string("master_ip") + "/hd/get_hash_data?path=" + urllib.parse.quote_plus(path))
    if json_data:
        json_obj = json.loads(json_data.decode())
        file = json_obj["file"]
        size = int(json_obj["size"])
        first = base64.b64decode(json_obj["first"])
        last = base64.b64decode(json_obj["last"])
        file = file.split("/")[-1]

        EventManager.throw_event(EventType.HashDataKnown, [size, file, first, last])
    else:
        Logger.write(2, "Failed to retrieve stream hash from master")


class YoutubeHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "search":
            data = yield YoutubeController.search(self.get_argument("query"), self.get_argument("type"))
            self.write(data)
        elif url == "home":
            data = yield YoutubeController.home()
            self.write(data)
        elif url == "channel_info":
            data = yield YoutubeController.channel_info(self.get_argument("id"))
            self.write(data)
        elif url == "channel_feed":
            data = yield YoutubeController.channel_feed(self.get_argument("id"))
            self.write(data)

    @gen.coroutine
    def post(self, url):
        if url == "play_youtube":
            YoutubeController.play_youtube(self.get_argument("id"), self.get_argument("title"))
        elif url == "play_youtube_url":
            YoutubeController.play_youtube_url(self.get_argument("url"), self.get_argument("title"))


class TorrentHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "top":
            self.write(TorrentController.top())
        elif url == "search":
            self.write(TorrentController.search(self.get_argument("keywords")))

    @gen.coroutine
    def post(self, url):
        if url == "play_torrent":
            TorrentController.play_torrent(self.get_argument("url"), self.get_argument("title"))


class RealtimeHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in TornadoServer.clients:
            Logger.write(2, "New connection")
            TornadoServer.clients.append(self)
            if TornadoServer.start_obj.torrent_manager.torrent and TornadoServer.start_obj.torrent_manager.torrent.state == TorrentState.WaitingUserFileSelection:
                if not Settings.get_bool("slave"):
                    watched_files = [f[9] for f in TornadoServer.start_obj.database.get_watched_torrent_files(TornadoServer.start_obj.torrent_manager.torrent.uri)]
                    files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, x.path in watched_files) for x in [y for y in TornadoServer.start_obj.torrent_manager.torrent.files if y.is_media]]
                else:
                    files = [MediaFile(x.path, x.name, x.length, x.season, x.episode, None, None, None, False) for x in [y for y in TornadoServer.start_obj.torrent_manager.torrent.files if y.is_media]]

                TornadoServer.broadcast('request', 'media_selection', files)

    def on_close(self):
        if self in TornadoServer.clients:
            Logger.write(2, "Connection closed")
            TornadoServer.clients.remove(self)


class DatabaseHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if Settings.get_bool("slave"):
            yield self.reroute_to_master()
            return

        if url == "get_favorites":
            Logger.write(2, "Getting favorites")
            self.write(to_JSON(TornadoServer.start_obj.database.get_favorites()))

        if url == "get_history":
            Logger.write(2, "Getting history")
            self.write(to_JSON(TornadoServer.start_obj.database.get_history()))

        if url == "get_unfinished_items":
            Logger.write(2, "Getting unfinished items")
            self.write(to_JSON(TornadoServer.start_obj.database.get_watching_items()))

    @gen.coroutine
    def post(self, url):
        if Settings.get_bool("slave"):
            yield self.reroute_to_master()
            return

        if url == "add_watched_torrent_file":
            Logger.write(2, "Adding to watched torrent files")
            TornadoServer.start_obj.database.add_watched_torrent_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("mediaFile"), self.get_argument("watchedAt"))

        if url == "add_watched_file":
            Logger.write(2, "Adding to watched files")
            TornadoServer.start_obj.database.add_watched_file(urllib.parse.unquote(self.get_argument("title")), urllib.parse.unquote(self.get_argument("url")), self.get_argument("watchedAt"))

        if url == "add_watched_youtube":
            Logger.write(2, "Adding to watched youtube")
            TornadoServer.start_obj.database.add_watched_youtube(
                self.get_argument("title"),
                self.get_argument("watchedAt"))

        if url == "add_watched_movie":
            Logger.write(2, "Adding to watched movie")
            TornadoServer.start_obj.database.add_watched_movie(
                self.get_argument("title"),
                self.get_argument("movieId"),
                self.get_argument("image"),
                self.get_argument("watchedAt"))

        if url == "add_watched_episode":
            Logger.write(2, "Adding to watched episodes")
            TornadoServer.start_obj.database.add_watched_episode(
                self.get_argument("title"),
                self.get_argument("showId"),
                self.get_argument("image"),
                self.get_argument("episodeSeason"),
                self.get_argument("episodeNumber"),
                self.get_argument("watchedAt"))

        if url == "remove_watched":
            Logger.write(2, "Remove watched")
            TornadoServer.start_obj.database.remove_watched(self.get_argument("id"))

        if url == "add_favorite":
            Logger.write(2, "Adding to favorites")
            TornadoServer.start_obj.database.add_favorite(self.get_argument("id"), self.get_argument("type"), self.get_argument("title"), self.get_argument("image"))

        if url == "remove_favorite":
            Logger.write(2, "Removing from favorites")
            TornadoServer.start_obj.database.remove_favorite(self.get_argument("id"))

        if url == "remove_unfinished":
            Logger.write(2, "Removing unfinished")
            TornadoServer.start_obj.database.remove_watching_item(
                urllib.parse.unquote(self.get_argument("url")))

        if url == "add_unfinished":
            Logger.write(2, "Adding unfinished")

            media_file = self.get_argument("mediaFile")
            if media_file == "None" or media_file == "null":
                media_file = None
            TornadoServer.start_obj.database.add_watching_item(
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

            TornadoServer.start_obj.database.update_watching_item(
                urllib.parse.unquote(self.get_argument("url")),
                int(self.get_argument("position")),
                self.get_argument("watchedAt"),
                media_file)

    @gen.coroutine
    def reroute_to_master(self):
        reroute = str(TornadoServer.master_ip) + self.request.uri
        Logger.write(2, "Sending request to master at " + reroute)
        result = yield RequestFactory.make_request_async(reroute, self.request.method)
        if result:
            self.write(result)
