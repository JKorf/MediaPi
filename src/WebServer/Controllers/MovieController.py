import sys
import urllib.parse
import urllib.request

import time
from tornado import gen

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from WebServer.Providers.Movies.PopcornMovieProvider import PopcornMovieProvider


class MovieController:

    movies_api_path = Settings.get_string("movie_api")
    sub_api_path = "http://api.yifysubtitles.com/subs/"
    sub_download_path = "http://yifysubtitles.com/"
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    @gen.coroutine
    def get_movies(page, orderby, keywords):
        if len(keywords) == 0:
            result = yield PopcornMovieProvider.get_list(page, orderby)
            return result
        else:
            result = yield PopcornMovieProvider.search(page, orderby, urllib.parse.quote(keywords))
            return result

    @staticmethod
    @gen.coroutine
    def get_movies_all(page, orderby, keywords):
        if len(keywords) == 0:
            result = yield PopcornMovieProvider.get_list(page, orderby, True)
            return result
        else:
            result = yield PopcornMovieProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return result

    @staticmethod
    @gen.coroutine
    def get_movie(id):
        result = yield PopcornMovieProvider.get_by_id(id)
        return result

    @staticmethod
    def play_movie(url, id, title, img):
        Logger.write(2, "Play movie: " + urllib.parse.unquote(title))

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.PreparePlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri, urllib.parse.unquote(img), 0, None])
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), None])

    @staticmethod
    @gen.coroutine
    def play_continue(delegate, type, url, title, image, position, media_file):
        Logger.write(2, "Continue " + title + " ("+type+") at " + str(position))
        url = urllib.parse.unquote_plus(url)
        img = urllib.parse.unquote(image)
        if img == "null":
            img = None
        if type == "torrent":
            EventManager.throw_event(EventType.StopTorrent, [])
            time.sleep(0.2)

            EventManager.throw_event(EventType.PreparePlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri, img, int(float(position)) * 1000, media_file])
            EventManager.throw_event(EventType.StartTorrent, [url, urllib.parse.unquote_plus(media_file)])
        else:
            if Settings.get_bool("slave"):
                yield delegate(url, title, int(float(position)) * 1000)
            else:
                if sys.platform == "linux" or sys.platform == "linux2":
                    if not url.startswith("/"):
                        url = "/" + url
                EventManager.throw_event(EventType.PreparePlayer, ["File", urllib.parse.unquote(title), url, img, int(float(position)) * 1000, url])
                EventManager.throw_event(EventType.StartPlayer, [])
