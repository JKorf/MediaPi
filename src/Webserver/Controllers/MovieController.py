import sys
import time
import urllib.parse
import urllib.request

from Webserver.Models import Media
from Webserver.Providers.Movies.PopcornMovieProvider import PopcornMovieProvider
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings


class MovieController:

    movies_api_path = Settings.get_string("movie_api")
    sub_api_path = "http://api.yifysubtitles.com/subs/"
    sub_download_path = "http://yifysubtitles.com/"
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    async def get_movies(page, orderby, keywords):
        if len(keywords) == 0:
            result = await PopcornMovieProvider.get_list(page, orderby)
            return result
        else:
            result = await PopcornMovieProvider.search(page, orderby, urllib.parse.quote(keywords))
            return result

    @staticmethod
    async def get_movies_all(page, orderby, keywords):
        if len(keywords) == 0:
            result = await PopcornMovieProvider.get_list(page, orderby, True)
            return result
        else:
            result = await PopcornMovieProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return result

    @staticmethod
    async def get_movie(id):
        result = await PopcornMovieProvider.get_by_id(id)
        return result

    @staticmethod
    def play_movie(url, id, title, img):
        Logger.write(2, "Play movie: " + urllib.parse.unquote(title))

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(0.2)
        EventManager.throw_event(EventType.PreparePlayer, [Media("Movie", id, urllib.parse.unquote(title), MovieController.server_uri, None, urllib.parse.unquote(img), 0)])
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), None])

    @staticmethod
    def play_continue(server, delegate, type, url, title, image, position, media_file):
        Logger.write(2, "Continue " + title + " ("+type+") at " + str(position))
        url = urllib.parse.unquote_plus(url)
        img = urllib.parse.unquote(image)
        if img == "null":
            img = None
        if type == "torrent":
            EventManager.throw_event(EventType.StopTorrent, [])
            time.sleep(0.2)
            file = urllib.parse.unquote_plus(media_file)
            if file == "null":
                file = None

            EventManager.throw_event(EventType.PreparePlayer, [Media("Movie", 0, urllib.parse.unquote(title), MovieController.server_uri, media_file, img, int(float(position)) * 1000)]) #TODO
            EventManager.throw_event(EventType.StartTorrent, [url, file])
        else:
            if Settings.get_bool("slave"):
                delegate(server, url, title, int(float(position)) * 1000)
            else:
                if sys.platform == "linux" or sys.platform == "linux2":
                    if not url.startswith("/"):
                        url = "/" + url
                EventManager.throw_event(EventType.PreparePlayer, [Media("File", 0, urllib.parse.unquote(title), url, url, img, int(float(position)) * 1000)])#TODO
                EventManager.throw_event(EventType.StartPlayer, [])