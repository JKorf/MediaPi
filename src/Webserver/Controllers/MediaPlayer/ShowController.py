import time
import urllib.parse
import urllib.request

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Webserver.Models import Media
from Webserver.Providers.ShowProvider import ShowProvider
from Webserver.BaseHandler import BaseHandler

class ShowController(BaseHandler):

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009/torrent"

    async def get(self, url):
        if url == "get_shows":
            data = await self.get_shows(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        if url == "get_shows_all":
            data = await self.get_shows_all(self.get_argument("page"), self.get_argument("orderby"),
                                                   self.get_argument("keywords"))
            self.write(data)
        elif url == "get_show":
            show = await self.get_show(self.get_argument("id"))
            self.write(show)

    async def get_shows(self, page, orderby, keywords):
        if len(keywords) == 0:
            response = await ShowProvider.get_list(page, orderby)
            return response
        else:
            response = await ShowProvider.search(page, orderby, urllib.parse.quote(keywords))
            return response

    async def get_shows_all(self, page, orderby, keywords):
        if len(keywords) == 0:
            response = await ShowProvider.get_list(page, orderby, True)
            return response
        else:
            response = await ShowProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return response

    async def get_show(self, id):
        response = await ShowProvider.get_by_id(id)
        return response