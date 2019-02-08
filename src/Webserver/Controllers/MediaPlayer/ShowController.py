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

    async def post(self, url):
        if url == "add_favorite":
            await self.add_favorite(self.get_argument("id"), self.get_argument("title"),self.get_argument("image"))
        elif url == "remove_favorite":
            await self.remove_favorite(self.get_argument("id"))

    async def get_shows(self, page, order_by, keywords):
        search_string = ""
        if keywords:
            search_string = "&keywords=" + urllib.parse.quote(keywords)
        data = await RequestFactory.make_request_async(ShowController.shows_api_path + "shows/" + page + "?sort=" + urllib.parse.quote(order_by) + search_string)

        if data is not None:
            return self.parse_show_data(data)
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ""

    async def get_by_id(self, id):
        Logger.write(2, "Get show by id " + id)
        response = await RequestFactory.make_request_async(ShowController.shows_api_path + "show/" + id)
        data = json.loads(response.decode('utf-8'))

        seen_episodes = Database().get_history_for_id(id)
        data['favorite'] = id in [x.id for x in Database().get_favorites()]
        for episode in data['episodes']:
            seen = [x for x in seen_episodes if episode['season'] == x.season and episode['episode'] == x.episode]
            episode['seen'] = len(seen) != 0
            if len(seen) == 0:
                continue
            seen = seen[-1]
            episode['seen'] = True
            episode['played_for'] = seen.played_for
            episode['length'] = seen.length
        return json.dumps(data).encode('utf-8')

    async def add_favorite(self, id, title, image):
        Logger.write(2, "Add show favorite: " + id)
        Database().add_favorite(id, "Show", title, image)

    async def remove_favorite(self, id):
        Logger.write(2, "Remove show favorite: " + id)
        Database().remove_favorite(id)

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
