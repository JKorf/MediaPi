from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import current_time, RequestFactory


class ShowProvider:

    shows_api_path = Settings.get_string("movie_api")
    shows_data = []

    @staticmethod
    def get_list(page, orderby):
        Logger.write(2, "Get shows list")
        data = RequestFactory.make_request(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + orderby)
        if data is not None:
            ShowProvider.shows_data = data
        else:
            EventManager.throw_event(EventType.Error, ["get_error", "Could not get shows data"])
            Logger.write(2, "Error fetching shows")
            return ShowProvider.shows_data

        return ShowProvider.shows_data

    @staticmethod
    def search(page, orderby, keywords):
        Logger.write(2, "Search shows " + keywords)
        return RequestFactory.make_request(ShowProvider.shows_api_path + "shows/"+page+"?sort=" + orderby + "&keywords="+keywords)

    @staticmethod
    def get_by_id(id):
        Logger.write(2, "Get show by id " + id)
        return RequestFactory.make_request(ShowProvider.shows_api_path + "show/" + id)