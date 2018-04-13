import os
import socket
import urllib.request

import tornado
from tornado import gen
from tornado import ioloop, web, websocket

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from TorrentSrc.Util.Threading import CustomThread
from Web.Server.Controllers.HDController import HDController
from Web.Server.Controllers.MovieController import MovieController
from Web.Server.Controllers.PlayerController import PlayerController
from Web.Server.Controllers.RadioController import RadioController
from Web.Server.Controllers.ShowController import ShowController
from Web.Server.Controllers.TorrentController import TorrentController
from Web.Server.Controllers.UtilController import UtilController
from Web.Server.Controllers.YoutubeController import YoutubeController
from Web.Server.Models import WebSocketMessage


class TornadoServer:
    start_obj = None
    master_ip = None
    clients = []

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
            (r"/torrents/(.*)", TorrentHandler),
            (r"/realtime", RealtimeHandler),
            (r"/database/(.*)", DatabaseHandler),
            (r"/(.*)", StaticFileHandler, {"path": os.getcwd() + "/Web", "default_filename": "index.html"})
        ]

        if not Settings.get_bool("slave"):
            handlers.append((r"/master/(.*)", StaticFileHandler, {"path": Settings.get_string("master_base_folder")}))

        self.application = web.Application(handlers)

        EventManager.register_event(EventType.PlayerStateChange, self.player_state_changed)
        EventManager.register_event(EventType.PlayerError, self.player_error)
        EventManager.register_event(EventType.Seek, self.player_seeking)
        EventManager.register_event(EventType.SetVolume, self.player_volume)
        EventManager.register_event(EventType.SetSubtitleId, self.player_subtitle_id)
        EventManager.register_event(EventType.SetSubtitleOffset, self.player_subtitle_offset)
        EventManager.register_event(EventType.SubsDoneChange, self.player_subs_done_change)
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
        try:
            reroute = str(TornadoServer.master_ip) + url
            Logger.write(2, "Sending notification to master at " + reroute)
            urllib.request.urlopen(reroute).read()
        except Exception as e:
            Logger.write(2, "Failed to notify master: " + str(e))

    def get_actual_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip + ":" + str(self.port)

    def player_state_changed(self, old_state, state):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'state_change', state.value)))

    def player_started(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'started', "")))

    def player_opening(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'opening', "")))

    def player_buffering(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'buffering', "")))

    def player_buffering_done(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'buffering_done', "")))

    def player_nothing_special(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'nothing_special', "")))

    def player_stopped(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'stopped', "")))

    def player_paused(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'paused', "")))

    def player_error(self):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'error', "")))

    def player_seeking(self, pos):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'seek', pos / 1000)))

    def player_volume(self, vol):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'volume', vol)))

    def player_subtitle_id(self, id):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'subtitle_id', id)))

    def player_subs_done_change(self, done):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'subs_done_change', done)))

    def player_subtitle_offset(self, offset):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('player_event', 'subtitle_offset', float(offset) / 1000 / 1000)))

    def application_error(self, error_type, error_message):
        for client in self.clients:
            client.write_message(to_JSON(WebSocketMessage('error_event', error_type, error_message)))


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
            self.finish()
        elif url == "debug":
            self.write(UtilController.debug(TornadoServer.start_obj))
        elif url == "startup":
            self.write(UtilController.startup())
        elif url == "info":
            self.write(UtilController.info())
        elif url == "get_settings":
            self.write(UtilController.get_settings())
        elif url == "version":
            self.write(UtilController.version())
        elif url == "status":
            self.write(UtilController.status(TornadoServer.start_obj))

    @gen.coroutine
    def post(self, url):
        if url == "save_settings":
            UtilController.save_settings(self.get_argument("raspberry"), self.get_argument("gui"), self.get_argument("external_trackers"), self.get_argument("max_subs"))
        elif url == "shutdown":
            UtilController.shutdown(TornadoServer.start_obj)
        elif url == "restart_pi":
            UtilController.restart_pi(TornadoServer.start_obj)
        elif url == "restart_app":
            UtilController.restart_app()
        elif url == "exit":
            UtilController.exit(TornadoServer.start_obj)
        elif url == "test":
            UtilController.test(TornadoServer.start_obj)
        elif url == "update":
            UtilController.update(TornadoServer.start_obj)


class MovieHandler(web.RequestHandler):
    @gen.coroutine
    def post(self, url):
        if url == "play_movie":
            MovieController.play_movie(self.get_argument("url"), self.get_argument("id"), self.get_argument("title"), self.get_argument("img", ""))
        elif url == "play_direct_link":
            MovieController.play_direct_link(self.get_argument("url"), self.get_argument("title"))
        elif url == "play_continue":
            MovieController.play_continue(self.get_argument("url"), self.get_argument("title"), self.get_argument("image"), self.get_argument("position"))

    @gen.coroutine
    def get(self, url):
        if url == "get_movies":
            data = yield(MovieController.get_movies(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords")))
            self.write(data)
            self.finish()
        if url == "get_movies_all":
            data = yield (MovieController.get_movies_all(self.get_argument("page"), self.get_argument("orderby"),
                                                     self.get_argument("keywords")))
            self.write(data)
            self.finish()
        elif url == "get_movie":
            data = yield (MovieController.get_movie(self.get_argument("id")))
            self.write(data)
            self.finish()
        elif url == "play_from_extension":
            MovieController.play_direct_link(self.get_argument("url"), self.get_argument("title"))



class ShowHandler(web.RequestHandler):
    @gen.coroutine
    def post(self, url):
        if url == "play_episode":
            ShowController.play_episode(self.get_argument("url"), self.get_argument("title"), self.get_argument("img", ""))

    @gen.coroutine
    def get(self, url):
        if url == "get_shows":
            data = yield (ShowController.get_shows(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords")))
            self.write(data)
            self.finish()
        if url == "get_shows_all":
            data = yield (ShowController.get_shows_all(self.get_argument("page"), self.get_argument("orderby"),
                                                   self.get_argument("keywords")))
            self.write(data)
            self.finish()
        elif url == "get_show":
            self.write(ShowController.get_show(self.get_argument("id")))
        elif url == "play_episode":
            ShowController.play_episode(self.get_argument("url"), self.get_argument("title"), self.get_argument("img", ""))

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
            PlayerController.stop_player()
        elif url == "pause_resume_player":
            PlayerController.pause_resume_player()
        elif url == "change_volume":
            PlayerController.change_volume(self.get_argument("vol"))
        elif url == "change_subtitle_offset":
            PlayerController.change_subtitle_offset(self.get_argument("offset"))
        elif url == "search_subs":
            PlayerController.search_subs()
        elif url == "seek":
            PlayerController.seek(self.get_argument("pos"))
        elif url == "set_audio_id":
            PlayerController.set_audio_track(self.get_argument("track"))


class HDHandler(web.RequestHandler):
    def get(self, url):
        if url == "drives":
            self.write(HDController.drives())
        elif url == "directory":
            self.write(HDController.directory(self.get_argument("path")))

    def post(self, url):
        if url == "play_file":
            HDController.play_file(self.get_argument("filename"), self.get_argument("path"))
        elif url == "next_image":
            HDController.next_image(self.get_argument("current_path"))
        elif url == "prev_image":
            HDController.prev_image(self.get_argument("current_path"))


class YoutubeHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "search":
            self.write(YoutubeController.search(self.get_argument("query")))
        elif url == "subscription_feed":
            data = yield (YoutubeController.subscription_feed())
            self.write(data)
            self.finish()

    @gen.coroutine
    def post(self, url):
        if url == "play_youtube":
            YoutubeController.play_youtube(self.get_argument("id"), self.get_argument("title"))
        elif url == "play_youtube_url":
            YoutubeController.play_youtube_url(self.get_argument("url"), self.get_argument("title"))

    def get_done(self, data):
        self.finish(data)


class TorrentHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if url == "get":
            self.write(TorrentController.get_torrents(TornadoServer.start_obj))

    @gen.coroutine
    def post(self, url):
        if url == "download":
            TorrentController.download(self.get_argument("url"), self.get_argument("title"))
        if url == "remove":
            TorrentController.remove(TornadoServer.start_obj, self.get_argument("id"))


class RealtimeHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in TornadoServer.clients:
            Logger.write(2, "New connection")
            TornadoServer.clients.append(self)

    def on_close(self):
        if self in TornadoServer.clients:
            Logger.write(2, "Connection closed")
            TornadoServer.clients.remove(self)


class DatabaseHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, url):
        if Settings.get_bool("slave"):
            self.reroute_to_master()
            return

        if url == "add_favorite":
            Logger.write(2, "Adding to favorites")
            TornadoServer.start_obj.database.add_favorite(self.get_argument("id"))

        if url == "remove_favorite":
            Logger.write(2, "Removing from favorites")
            TornadoServer.start_obj.database.remove_favorite(self.get_argument("id"))

        if url == "get_favorites":
            Logger.write(2, "Getting favorites")
            self.write(to_JSON(TornadoServer.start_obj.database.get_favorites()))

        if url == "add_watched_file":
            Logger.write(2, "Adding to watched files")
            TornadoServer.start_obj.database.add_watched_file(self.get_argument("url"), self.get_argument("watchedAt"))

        if url == "get_watched_files":
            Logger.write(2, "Getting watched files")
            self.write(to_JSON(TornadoServer.start_obj.database.get_watched_files()))

        if url == "add_watched_episode":
            Logger.write(2, "Adding to watched episodes")
            TornadoServer.start_obj.database.add_watched_episode(
                self.get_argument("showId"),
                self.get_argument("episodeSeason"),
                self.get_argument("episodeNumber"),
                self.get_argument("watchedAt"))

        if url == "get_watched_episodes":
            Logger.write(2, "Getting watched episodes")
            self.write(to_JSON(TornadoServer.start_obj.database.get_watched_episodes()))

        if url == "get_unfinished_torrents":
            Logger.write(2, "Getting unfinished torrents")
            self.write(to_JSON(TornadoServer.start_obj.database.get_watching_torrents()))

        if url == "remove_unfinished":
            Logger.write(2, "Removing unfinished")
            TornadoServer.start_obj.database.remove_watching_torrent(
                self.get_argument("url"))

        if url == "add_unfinished":
            Logger.write(2, "Adding unfinished")
            TornadoServer.start_obj.database.add_watching_torrent(
                self.get_argument("name"),
                self.get_argument("url"),
                self.get_argument("image"),
                int(self.get_argument("length")),
                self.get_argument("time"))

        if url == "update_unfinished":
            Logger.write(2, "Updating unfinished")
            TornadoServer.start_obj.database.update_watching_torrent(
                self.get_argument("url"),
                int(self.get_argument("position")))

    def reroute_to_master(self):
        reroute = str(TornadoServer.master_ip) + self.request.uri
        Logger.write(2, "Sending request to master at " + reroute)
        self.write(urllib.request.urlopen(reroute).read())