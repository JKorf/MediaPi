import json

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Models import BaseMedia
from Webserver.BaseHandler import BaseHandler

class ShowController(BaseHandler):

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009/torrent"

    async def get(self, url):
        if url == "get_shows":
            data = await self.get_shows(self.get_argument("page"), self.get_argument("orderby"), self.get_argument("keywords"))
            self.write(data)
        elif url == "get_show":
            show = await self.get_by_id(self.get_argument("id"))
            self.write(show)

    async def get_shows(self, page, order_by, keywords):
        search_string = ""
        if keywords:
            search_string = "&keywords=" + keywords
        data = await RequestFactory.make_request_async(ShowController.shows_api_path + "shows/" + page + "?sort=" + order_by + search_string)

        if data is not None:
            return self.parse_show_data(data)
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ""

    async def get_by_id(self, id):
        Logger.write(2, "Get show by id " + id)
        response = await RequestFactory.make_request_async(ShowController.shows_api_path + "show/" + id)
        return response

    @staticmethod
    def parse_show_data(data):
        json_data = json.loads(data)
        if isinstance(json_data, list):
            return to_JSON([Show(x['imdb_id'], x['images']['poster'], x['title'], x['rating']['percentage']) for x in json_data]).encode()
        else:
            return to_JSON(Show(json_data['imdb_id'], json_data['images']['poster'], json_data['title'], json_data['rating']['percentage'])).encode()


class Show(BaseMedia):

    def __init__(self, id, poster, title, rating):
        super().__init__(id, poster, title)
        self.rating = rating
