import json

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON


class ShowProvider:

    shows_api_path = Settings.get_string("movie_api")
    shows_data = []

    @staticmethod
    async def get_list(page, order_by, get_all=False):
        Logger.write(2, "Get shows list")
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/" + str(i + 1) + "?sort=" + order_by)
                if new_data is not None:
                    data = ShowProvider.append_result(data, new_data)
        else:
            data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + order_by)

        if data is not None:
            ShowProvider.shows_data = ShowProvider.parse_show_data(data)
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ShowProvider.shows_data

        return ShowProvider.shows_data

    @staticmethod
    async def search(page, order_by, keywords, get_all=False):
        Logger.write(2, "Search shows " + keywords)
        if get_all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(
                    ShowProvider.shows_api_path + "shows/" + str(i + 1) + "?sort=" + order_by + "&keywords=" + keywords)
                if new_data is not None:
                    data = ShowProvider.append_result(data, new_data)
            return data
        else:
            data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + order_by + "&keywords="+keywords)
            return data

    @staticmethod
    async def get_by_id(id):
        Logger.write(2, "Get show by id " + id)
        response = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "show/" + id)
        return response

    @staticmethod
    def append_result(data, new_data):
        if len(data) != 0:
            data = data[:-1] + b"," + new_data[1:]
        else:
            data += new_data
        return data

    @staticmethod
    def parse_show_data(data):
        json_data = json.loads(data)
        return to_JSON([Show(x['imdb_id'], x['images']['poster'], x['title'], x['rating']['percentage']) for x in json_data]).encode()


class Show:

    def __init__(self, id, poster, title, rating):
        self.id = id
        self.poster = poster
        self.title = title
        self.rating = rating
