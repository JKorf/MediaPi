import json
import urllib.parse

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON


class PopcornMovieProvider:

    movies_api_path = Settings.get_string("movie_api")
    movies_data = None

    @staticmethod
    async def get_list(page, order_by, get_all=False):
        Logger.write(2, "Get movies list")
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+str(i + 1)+"?sort=" + urllib.parse.quote(order_by))
                if new_data is not None:
                    data = PopcornMovieProvider.append_result(data, new_data)
        else:
            data = await RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+page+"?sort=" + urllib.parse.quote(order_by))

        if data is not None:
            PopcornMovieProvider.movies_data = Movie.parse_list_from_popcorn_time(data.decode('utf-8')).encode('utf-8')
        else:
            Logger.write(2, "Error fetching movies")
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get Popcorn movies data"])

        return PopcornMovieProvider.movies_data

    @staticmethod
    async def search(page, orderby, keywords, get_all=False):
        Logger.write(2, "Search movies " + keywords)
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(
                    PopcornMovieProvider.movies_api_path + "movies/" + page + "?keywords=" + keywords + "&sort=" + urllib.parse.quote(
                        orderby))
                if new_data is not None:
                    data = PopcornMovieProvider.append_result(data, new_data)
            return Movie.parse_list_from_popcorn_time(data.decode('utf-8')).encode('utf-8')
        else:
            data = await RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+page+"?keywords="+keywords+"&sort="+urllib.parse.quote(orderby))
            return Movie.parse_list_from_popcorn_time(data.decode('utf-8')).encode('utf-8')

    @staticmethod
    async def get_by_id(id):
        Logger.write(2, "Get movie by id " + id)
        data = await RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movie/" + id)
        return Movie.parse_item_from_popcorn_time(data.decode('utf-8')).encode('utf-8')

    @staticmethod
    def append_result(data, new_data):
        if len(data) != 0:
            data = data[:-1] + b"," + new_data[1:]
        else:
            data += new_data
        return data

class Torrent:

    def __init__(self):
        self.url = None
        self.quality = None
        self.seeds = None
        self.peers = None
        self.size = None


class Movie:

    def __init__(self):
        self.id = None
        self.title = None
        self.year = None
        self.rating_percentage = None
        self.rating_grade = None
        self.runtime = None
        self.genres = None
        self.synopsis = None
        self.youtube_trailer = None
        self.poster = None
        self.torrents = []
        self.released = None

    @staticmethod
    def parse_list_from_popcorn_time(data):
        result = []
        json_data = json.loads(data)
        for movie_data in json_data:
            result.append(Movie.parse_popcorn_movie(movie_data))
        return to_JSON(result)

    @staticmethod
    def parse_item_from_popcorn_time(data):
        return to_JSON(Movie.parse_popcorn_movie(json.loads(data)))

    @staticmethod
    def parse_popcorn_movie(movie_data):
        movie = Movie()
        movie.id = movie_data['imdb_id']
        movie.title = movie_data['title']
        movie.year = movie_data['year']
        movie.rating = movie_data['rating']['percentage']
        movie.runtime = movie_data['runtime']
        movie.genres = movie_data['genres']
        movie.synopsis = movie_data['synopsis']
        movie.youtube_trailer = movie_data['trailer']
        if 'images' in movie_data:
            if 'poster' in movie_data['images']:
                movie.poster = movie_data['images']['poster']
            elif len(movie_data['images']) > 0:
              movie.poster = movie_data['images'][0]
            else:
                movie.poster = ""
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