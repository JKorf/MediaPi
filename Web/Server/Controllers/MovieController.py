import urllib.parse
import urllib.request

import time
from tornado.concurrent import return_future

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Enums import OutputMode
from Web.Server.Providers.Movies.YTSMovieProvider import YTSMovieProvider
from Web.Server.Providers.Movies.PopcornMovieProvider import PopcornMovieProvider


class MovieController:

    movies_api_path = Settings.get_string("movie_api")
    sub_api_path = "http://api.yifysubtitles.com/subs/"
    sub_download_path = "http://yifysubtitles.com/"
    server_uri = "http://localhost:50009"

    @staticmethod
    def get_provider():
        use_yts = Settings.get_bool("yts_movie_api")
        if use_yts:
            return YTSMovieProvider
        else:
            return PopcornMovieProvider

    @staticmethod
    @return_future
    def get_movies(page, orderby, keywords, callback=None):
        if len(keywords) == 0:
            callback(MovieController.get_provider().get_list(page, orderby))
        else:
            callback(MovieController.get_provider().search(page, orderby, urllib.parse.quote(keywords)))

    @staticmethod
    @return_future
    def get_movie(id, callback=None):
        callback(MovieController.get_provider().get_by_id(id))

    @staticmethod
    def play_movie(url, id, title, img):
        Logger.write(2, "Play movie: " + urllib.parse.unquote(title))

        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), OutputMode.Stream])
        EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri, urllib.parse.unquote(img)])
        EventManager.throw_event(EventType.IMDbKnown, [id])


    @staticmethod
    def play_direct_link(url, title):
        Logger.write(2, "Play direct link")
        url = urllib.parse.unquote_plus(url)

        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(1)
        if url.endswith('.torrent') or url.startswith('magnet:'):
            EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), OutputMode.Stream])
            EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri])
        else:
            EventManager.throw_event(EventType.StartPlayer, ["Movie", urllib.parse.unquote(title), urllib.parse.unquote_plus(url)])
