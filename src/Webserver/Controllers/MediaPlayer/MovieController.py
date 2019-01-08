import urllib.parse
import urllib.request

from Shared.Settings import Settings
from Webserver.Providers.MovieProvider import MovieProvider
from Webserver.BaseHandler import BaseHandler


class MovieController(BaseHandler):

    movies_api_path = Settings.get_string("movie_api")
    sub_api_path = "http://api.yifysubtitles.com/subs/"
    sub_download_path = "http://yifysubtitles.com/"
    server_uri = "http://localhost:50009/torrent"

    async def get(self, url):
        if url == "get_movies":
            data = await self.get_movies(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_movies_all":
            data = await self.get_movies_all(self.get_argument("page"), self.get_argument("orderby"),
                                                     self.get_argument("keywords"))
            self.write(data)
        elif url == "get_movie":
            data = await self.get_movie(self.get_argument("id"))
            self.write(data)

    async def get_movies(self, page, orderby, keywords):
        if len(keywords) == 0:
            result = await MovieProvider.get_list(page, orderby)
            return result
        else:
            result = await MovieProvider.search(page, orderby, urllib.parse.quote(keywords))
            return result

    async def get_movies_all(self, page, orderby, keywords):
        if len(keywords) == 0:
            result = await MovieProvider.get_list(page, orderby, True)
            return result
        else:
            result = await MovieProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return result

    async def get_movie(self, id):
        result = await MovieProvider.get_by_id(id)
        return result