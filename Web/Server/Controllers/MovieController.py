import sys
import urllib.parse
import urllib.request

import time
from tornado import gen

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Web.Server.Providers.Movies.PopcornMovieProvider import PopcornMovieProvider


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
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url)])
        EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri, urllib.parse.unquote(img)])


    @staticmethod
    def play_direct_link(url, title):
        Logger.write(2, "Play direct link")
        url = urllib.parse.unquote_plus(url)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(1)
        if url.endswith('.torrent') or url.startswith('magnet:'):
            EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url)])
            EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri])
        else:
            EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), urllib.parse.unquote_plus(url)])

    @staticmethod
    @gen.coroutine
    def play_continue(delegate, type, url, title, image, position):
        Logger.write(2, "Continue " + title + "("+type+") at " + str(position))
        url = urllib.parse.unquote_plus(url)
        if type == "torrent":
            EventManager.throw_event(EventType.StopTorrent, [])
            time.sleep(0.2)
            EventManager.throw_event(EventType.StartTorrent, [url])
            EventManager.throw_event(EventType.StartPlayer,
                                     ["Movie",
                                      urllib.parse.unquote(title),
                                      MovieController.server_uri,
                                      urllib.parse.unquote(image),
                                      int(float(position)) * 1000])
        else:
            if Settings.get_bool("slave"):
                yield delegate(url, title, int(float(position)) * 1000)
            else:
                if sys.platform == "linux" or sys.platform == "linux2":
                    if not url.startswith("/"):
                        url = "/" + url
                EventManager.throw_event(EventType.StartPlayer,
                                         ["File",
                                          urllib.parse.unquote(title),
                                          url,
                                          urllib.parse.unquote(image),
                                          int(float(position)) * 1000])
