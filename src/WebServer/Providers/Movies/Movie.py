import json

from Shared.Util import to_JSON


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
        self.imdb_id = None
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
        movie.id = movie_data['_id']
        movie.imdb_id = movie_data['imdb_id']
        movie.title = movie_data['title']
        movie.year = movie_data['year']
        movie.rating_percentage = movie_data['rating']['percentage']
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