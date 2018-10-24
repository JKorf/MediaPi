from tornado import gen

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import RequestFactory


class ShowProvider:

    shows_api_path = Settings.get_string("movie_api")
    shows_data = []

    @staticmethod
    async def get_list(page, orderby, all=False):
        Logger.write(2, "Get shows list")
        if all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/" + str(i + 1) + "?sort=" + orderby)
                if new_data is not None:
                    data = ShowProvider.append_result(data, new_data)
        else:
            data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + orderby)

        if data is not None:
            ShowProvider.shows_data = data
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ShowProvider.shows_data

        return ShowProvider.shows_data

    @staticmethod
    async def search(page, orderby, keywords, all=False):
        Logger.write(2, "Search shows " + keywords)
        if all:
            data = b""
            for i in range(int(page)):
                new_data = await RequestFactory.make_request_async(
                    ShowProvider.shows_api_path + "shows/" + str(i + 1) + "?sort=" + orderby + "&keywords=" + keywords)
                if new_data is not None:
                    data = ShowProvider.append_result(data, new_data)
            return data
        else:
            data = await RequestFactory.make_request_async(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + orderby + "&keywords="+keywords)
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