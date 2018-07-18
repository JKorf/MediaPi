import urllib.parse

import time

from tpb import CATEGORIES

from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Util import to_JSON
from Web.Server.Controllers.MovieController import MovieController
from Web.Server.Models import TorrentModel

from tpb import TPB, ORDERS


class TorrentController:
    @staticmethod
    def top():
        t = TPB('https://pirateahoy.net/')
        result = []
        for torrent in t.top(CATEGORIES.VIDEO):
            result.append(TorrentModel(torrent.title, torrent.magnet_link, torrent.seeders, torrent.leechers, torrent.size, torrent.sub_category))

        return to_JSON(result)

    @staticmethod
    def search(keywords):
        t = TPB('https://pirateahoy.net/')
        result = []
        for torrent in t.search(urllib.parse.unquote(keywords)).category(CATEGORIES.VIDEO).order(ORDERS.SEEDERS.DES):
            result.append(TorrentModel(torrent.title, torrent.magnet_link, torrent.seeders, torrent.leechers, torrent.size, torrent.sub_category))
        return to_JSON(result)

    @staticmethod
    def play_torrent(url, title):
        Logger.write(2, "Play direct link")
        url = urllib.parse.unquote_plus(url)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(1)
        if url.endswith('.torrent') or url.startswith('magnet:'):
            EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url)])
            EventManager.throw_event(EventType.StartPlayer,
                                     ["Movie", urllib.parse.unquote(title), MovieController.server_uri])
        else:
            EventManager.throw_event(EventType.StartPlayer,
                                     ["Movie", urllib.parse.unquote(title), urllib.parse.unquote_plus(url)])
