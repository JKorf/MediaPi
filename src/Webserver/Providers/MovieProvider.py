import json
import urllib.parse

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Models import BaseMedia


class MovieProvider:

    movies_api_path = Settings.get_string("movie_api")
    movies_data = None

    @staticmethod
    async def get_list(page, order_by, get_all=False):
        Logger.write(2, "Get movies list")
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(MovieProvider.movies_api_path + "movies/"+str(i + 1)+"?sort=" + urllib.parse.quote(order_by))
                if new_data is not None:
                    data = MovieProvider.append_result(data, new_data)
        else:
            data = await RequestFactory.make_request_async(MovieProvider.movies_api_path + "movies/"+page+"?sort=" + urllib.parse.quote(order_by))

        if data is not None:
            MovieProvider.movies_data = MovieProvider.parse_movie_data(data.decode('utf-8'))
        else:
            Logger.write(2, "Error fetching movies")
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get Popcorn movies data"])

        return MovieProvider.movies_data

    @staticmethod
    async def search(page, orderby, keywords, get_all=False):
        Logger.write(2, "Search movies " + keywords)
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(
                    MovieProvider.movies_api_path + "movies/" + page + "?keywords=" + keywords + "&sort=" + urllib.parse.quote(
                        orderby))
                if new_data is not None:
                    data = MovieProvider.append_result(data, new_data)
            return MovieProvider.parse_movie_data(data.decode('utf-8'))
        else:
            data = await RequestFactory.make_request_async(MovieProvider.movies_api_path + "movies/"+page+"?keywords="+keywords+"&sort="+urllib.parse.quote(orderby))
            return MovieProvider.parse_movie_data(data.decode('utf-8'))

    @staticmethod
    async def get_by_id(id):
        Logger.write(2, "Get movie by id " + id)
        data = await RequestFactory.make_request_async(MovieProvider.movies_api_path + "movie/" + id)
        return data

    @staticmethod
    def append_result(data, new_data):
        if len(data) != 0:
            data = data[:-1] + b"," + new_data[1:]
        else:
            data += new_data
        return data

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