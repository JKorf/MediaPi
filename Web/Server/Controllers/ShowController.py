import urllib.request
import urllib.parse

import time
from tornado.concurrent import return_future

from Shared.Events import EventManager, EventType
from Shared.Logger import Logger
from Shared.Settings import Settings
from TorrentSrc.Util.Enums import OutputMode
from Web.Server.Providers.ShowProvider import ShowProvider


class ShowController:

    shows_api_path = Settings.get_string("serie_api")
    server_uri = "http://localhost:50009"

    @staticmethod
    @return_future
    def get_shows(page, orderby, keywords, callback=None):
        if len(keywords) == 0:
            callback(ShowProvider.get_list(page, orderby))
        else:
            callback(ShowProvider.search(page, orderby, urllib.parse.quote(keywords)))

    @staticmethod
    def get_show(id):
        return ShowProvider.get_by_id(id)

    @staticmethod
    def play_episode(url, title, img):
        Logger.write(2, "Play epi: " + url)

        EventManager.throw_event(EventType.StopStreamTorrent, [])
        time.sleep(1)
        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), OutputMode.Stream])
        EventManager.throw_event(EventType.StartPlayer, ["Show", urllib.parse.unquote(title), ShowController.server_uri, urllib.parse.unquote(img)])