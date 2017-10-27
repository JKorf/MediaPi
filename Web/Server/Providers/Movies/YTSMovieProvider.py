from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time, RequestFactory
from Web.Server.Providers.Movies.Movie import Movie


class YTSMovieProvider:

    api_url = "https://yts.ag/api/v2/"

    @staticmethod
    def get_list(page, orderby):
        if orderby == 'last added':
            orderby = 'date_added'
        if orderby == 'trending':
            orderby = 'like_count'

        Logger.write(2, "Requesting movie data")
        data = RequestFactory.make_request(YTSMovieProvider.api_url + "list_movies.json?sort_by="+orderby+"&limit=50&page="+page)
        if data is not None:
            return Movie.parse_list_from_yts(data.decode('utf-8'))
        else:
            Logger.write(2, "Error fetching movies")
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get YTS movies data"])
            return None

    @staticmethod
    def search(page, orderby, keywords):
        Logger.write(2, "Search movies " + keywords)
        return Movie.parse_list_from_yts(RequestFactory.make_request(YTSMovieProvider.api_url + "list_movies.json?query_term=" + keywords+"&sort_by="+orderby+"&limit=50&page="+page).decode('utf-8')).encode('utf-8')

    @staticmethod
    def get_by_id(id):
        Logger.write(2, "Get movie by id " + id)
        return Movie.parse_item_from_yts(RequestFactory.make_request(YTSMovieProvider.api_url + "movie_details/json?movie_id=" + id).decode('utf-8')).encode('utf-8')
