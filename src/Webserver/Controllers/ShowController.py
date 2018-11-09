import time
import urllib.parse
import urllib.request

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Webserver.Models import Media
from Webserver.Providers.ShowProvider import ShowProvider


class ShowController:

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    async def get_shows(page, orderby, keywords):
        if len(keywords) == 0:
            response = await ShowProvider.get_list(page, orderby)
            return response
        else:
            response = await ShowProvider.search(page, orderby, urllib.parse.quote(keywords))
            return response

    @staticmethod
    async def get_shows_all(page, orderby, keywords):
        if len(keywords) == 0:
            response = await ShowProvider.get_list(page, orderby, True)
            return response
        else:
            response = await ShowProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return response

    @staticmethod
    async def get_show(id):
        response = await ShowProvider.get_by_id(id)
        return response

    @staticmethod
    def play_episode(url, id, title, img, season, episode):
        Logger.write(2, "Play epi: " + url)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(1)
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), None])
        EventManager.throw_event(EventType.PreparePlayer, [Media("Show", id, urllib.parse.unquote(title), ShowController.server_uri, None, urllib.parse.unquote(img), 0, season, episode)])