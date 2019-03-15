import json
import urllib.parse

from flask import request

from Database.Database import Database
from Shared.Events import EventManager, EventType
from Shared.Logger import Logger, LogVerbosity
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import BaseMedia


class MovieController:

    movies_api_path = Settings.get_string("movie_api")
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    @app.route('/movies', methods=['GET'])
    def get_movies():
        page = int(request.args.get('page'))
        order_by = request.args.get('orderby')
        keywords = request.args.get('keywords')
        include_previous_pages = request.args.get('page') == "true"
        search_string = ""
        if keywords:
            search_string = "&keywords=" + urllib.parse.quote(keywords)

        if include_previous_pages:
            data = []
            current_page = 0
            while current_page != page:
                current_page+= 1
                data += MovieController.request_movies(
                    MovieController.movies_api_path + "movies/" + str(current_page) + "?sort=" + urllib.parse.quote(
                        order_by) + search_string)

        else:
            data = MovieController.request_movies(MovieController.movies_api_path + "movies/" + str(page) + "?sort=" + urllib.parse.quote(order_by) + search_string)

        return to_JSON(data).encode()

    @staticmethod
    def request_movies(url):
        data = RequestFactory.make_request(url)

        if data is not None:
            return MovieController.parse_movie_data(data.decode('utf-8'))
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get movie data"])
            Logger().write(LogVerbosity.Info, "Error fetching movies")
            return []

    @staticmethod
    @app.route('/movie', methods=['GET'])
    def get_movie_by_id():
        id = request.args.get('id')
        Logger().write(LogVerbosity.Debug, "Get movie by id " + id)
        response = RequestFactory.make_request(MovieController.movies_api_path + "movie/" + id)
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
            return [Movie.parse_movie(x) for x in json_data]
        else:
            return Movie.parse_movie(json_data)


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