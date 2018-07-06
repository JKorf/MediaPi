import urllib.request
import urllib.parse

import time
from tornado import gen

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from Web.Server.Providers.ShowProvider import ShowProvider


class ShowController:

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009/torrent"

    @staticmethod
    @gen.coroutine
    def get_shows(page, orderby, keywords):
        if len(keywords) == 0:
            response = yield ShowProvider.get_list(page, orderby)
            return response
        else:
            response = yield ShowProvider.search(page, orderby, urllib.parse.quote(keywords))
            return response

    @staticmethod
    @gen.coroutine
    def get_shows_all(page, orderby, keywords):
        if len(keywords) == 0:
            response = yield ShowProvider.get_list(page, orderby, True)
            return response
        else:
            response = yield ShowProvider.search(page, orderby, urllib.parse.quote(keywords), True)
            return response

    @staticmethod
    @gen.coroutine
    def get_show(id):
        response = yield ShowProvider.get_by_id(id)
        return response

    @staticmethod
    def play_episode(url, title, img):
        Logger.write(2, "Play epi: " + url)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(1)
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url)])
        EventManager.throw_event(EventType.StartPlayer, ["Show", urllib.parse.unquote(title), ShowController.server_uri, urllib.parse.unquote(img)])