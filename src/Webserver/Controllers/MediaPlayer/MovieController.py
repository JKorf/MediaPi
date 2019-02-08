import json
import urllib.parse

from Database.Database import Database
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Models import BaseMedia
from Webserver.BaseHandler import BaseHandler

class MovieController(BaseHandler):

    movies_api_path = Settings.get_string("movie_api")
    server_uri = "http://localhost:50009/torrent"

    async def get(self, url):
        if url == "get_movies":
            data = await self.get_movies(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        elif url == "get_movie":
            show = await self.get_by_id(self.get_argument("id"))
            self.write(show)

    async def get_movies(self, page, order_by, keywords):
        search_string = ""
        if keywords:
            search_string = "&keywords=" + urllib.parse.quote(keywords)
        data = await RequestFactory.make_request_async(MovieController.movies_api_path + "movies/" + page + "?sort=" + urllib.parse.quote(order_by) + search_string)

        if data is not None:
            return self.parse_movie_data(data)
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ""

    async def get_by_id(self, id):
        Logger.write(2, "Get movie by id " + id)
        response = await RequestFactory.make_request_async(MovieController.movies_api_path + "movie/" + id)
        data = json.loads(response.decode('utf-8'))

        seen = Database().get_history_for_id(id)
        data['seen'] = len(seen) > 0
        if len(seen) > 0:
            seen = seen[-1]
            data['played_for'] = seen.played_for
            data['length'] = seen.length

        return json.dumps(data).encode('utf-8')

    @staticmethod
    def parse_movie_data(data):
        json_data = json.loads(data)
        if isinstance(json_data, list):
            return to_JSON([Movie.parse_movie(x) for x in json_data]).encode()
        else:
            return to_JSON(Movie.parse_movie(json_data)).encode()


class Torrent:

    def __init__(self):
        self.url = None
        self.quality = None
        self.seeds = None
        self.peers = None
        self.size = None


class Movie(BaseMedia):

    def __init__(self, id, poster, title):
        super().__init__(id, poster, title)
        self.year = None
        self.rating = 0
        self.runtime = None
        self.genres = None
        self.synopsis = None
        self.youtube_trailer = None
        self.torrents = []
        self.released = None

    @staticmethod
    def parse_movie(movie_data):
        poster = ""
        if 'images' in movie_data:
            if 'poster' in movie_data['images']:
                poster = movie_data['images']['poster']
            elif len(movie_data['images']) > 0:
                poster = movie_data['images'][0]

        movie = Movie(
            movie_data['imdb_id'],
            poster,
            movie_data['title'])

        movie.rating = movie_data['rating']['percentage']
        movie.year = movie_data['year']
        movie.runtime = movie_data['runtime']
        movie.genres = movie_data['genres']
        movie.synopsis = movie_data['synopsis']
        movie.youtube_trailer = movie_data['trailer']
        movie.released = movie_data['released']
        movie.torrents = []
        for torrent_data in movie_data['torrents']['en']:
            torrent = Torrent()
            torrent.quality = torrent_data
            torrent_data = movie_data['torrents']['en'][torrent_data]
            torrent.url = torrent_data['url']
            torrent.seeds = torrent_data['seed']
            torrent.peers = torrent_data['peer']
            if 'size' in torrent_data:
                torrent.size = torrent_data['size']
            elif 'filesize' in torrent_data:
                torrent.size = torrent_data['filesize']
            movie.torrents.append(torrent)

        return movie