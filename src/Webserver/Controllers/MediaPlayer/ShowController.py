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
            data = await self.get_shows(int(self.get_argument("page")), self.get_argument("orderby"), self.get_argument("keywords"), self.get_argument("include_previous") == "true")
            self.write(data)
        elif url == "get_show":
            show = await self.get_by_id(self.get_argument("id"))
            self.write(show)

    async def post(self, url):
        if url == "add_favorite":
            await self.add_favorite(self.get_argument("id"), self.get_argument("title"),self.get_argument("image"))
        elif url == "remove_favorite":
            await self.remove_favorite(self.get_argument("id"))

    @staticmethod
    async def get_shows(page, order_by, keywords, include_previous_pages):
        search_string = ""
        if keywords:
            search_string = "&keywords=" + urllib.parse.quote(keywords)

        if include_previous_pages:
            data = []
            current_page = 0
            while current_page != page:
                current_page+= 1
                data += await ShowController.request_shows(
                    ShowController.shows_api_path + "shows/" + str(current_page) + "?sort=" + urllib.parse.quote(
                        order_by) + search_string)

        else:
            data = await ShowController.request_shows(ShowController.shows_api_path + "shows/" + str(page) + "?sort=" + urllib.parse.quote(order_by) + search_string)

        return to_JSON(data).encode()

    @staticmethod
    async def request_shows(url):
        data = await RequestFactory.make_request_async(url)

        if data is not None:
            return ShowController.parse_show_data(data.decode('utf-8'))
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get show data"])
            Logger().write(2, "Error fetching shows")
            return []

    @staticmethod
    async def get_by_id(id):
        Logger().write(2, "Get show by id " + id)
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

    @staticmethod
    async def add_favorite(id, title, image):
        Logger().write(2, "Add show favorite: " + id)
        Database().add_favorite(id, "Show", title, image)

    @staticmethod
    async def remove_favorite(id):
        Logger().write(2, "Remove show favorite: " + id)
        Database().remove_favorite(id)

    @staticmethod
    def parse_show_data(data):
        json_data = json.loads(data)
        if isinstance(json_data, list):
            return [Show(x['imdb_id'], ShowController.get_poster(x), x['title'], x['rating']['percentage']) for x in json_data]
        else:
            return Show(json_data['imdb_id'], ShowController.get_poster(json_data), json_data['title'], json_data['rating']['percentage'])

    @staticmethod
    def get_poster(show):
        poster = ""
        if 'images' in show:
            if 'poster' in show['images']:
                poster = show['images']['poster']
            elif len(show['images']) > 0:
                poster = show['images'][0]
        return poster

class Show(BaseMedia):

    def __init__(self, id, poster, title, rating):
        super().__init__(id, poster, title)
        self.rating = rating
