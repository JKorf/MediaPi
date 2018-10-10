import urllib.parse

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import RequestFactory
from WebServer.Providers.Movies.Movie import Movie
from tornado import gen


class PopcornMovieProvider:

    movies_api_path = Settings.get_string("movie_api")
    movies_data = None

    @staticmethod
    @gen.coroutine
    def get_list(page, orderby, all=False):
        Logger.write(2, "Get movies list")
        if all:
            data = b""
            for i in range(int(page)):
                new_data = yield RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+str(i + 1)+"?sort=" + urllib.parse.quote(orderby))
                if new_data is not None:
                    data = PopcornMovieProvider.append_result(data, new_data)
        else:
            data = yield RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+page+"?sort=" + urllib.parse.quote(orderby))

        if data is not None:
            PopcornMovieProvider.movies_data = data
        else:
            Logger.write(2, "Error fetching movies")
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get Popcorn movies data"])

        return Movie.parse_list_from_popcorn_time(PopcornMovieProvider.movies_data.decode('utf-8')).encode('utf-8')

    @staticmethod
    @gen.coroutine
    def search(page, orderby, keywords, all=False):
        Logger.write(2, "Search movies " + keywords)
        if all:
            data = b""
            for i in range(int(page)):
                new_data = yield RequestFactory.make_request_async(
                    PopcornMovieProvider.movies_api_path + "movies/" + page + "?keywords=" + keywords + "&sort=" + urllib.parse.quote(
                        orderby))
                if new_data is not None:
                    data = PopcornMovieProvider.append_result(data, new_data)
            return Movie.parse_list_from_popcorn_time(data.decode('utf-8')).encode('utf-8')
        else:
            data = yield RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movies/"+page+"?keywords="+keywords+"&sort="+urllib.parse.quote(orderby))
            return Movie.parse_list_from_popcorn_time(data.decode('utf-8')).encode('utf-8')

    @staticmethod
    @gen.coroutine
    def get_by_id(id):
        Logger.write(2, "Get movie by id " + id)
        data = yield RequestFactory.make_request_async(PopcornMovieProvider.movies_api_path + "movie/" + id)
        return Movie.parse_item_from_popcorn_time(data.decode('utf-8')).encode('utf-8')

    @staticmethod
    def append_result(data, new_data):
        if len(data) != 0:
            data = data[:-1] + b"," + new_data[1:]
        else:
            data += new_data
        return data
