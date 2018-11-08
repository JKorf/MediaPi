import time
import urllib.parse

from UI.Web.Server.Models import TorrentModel
from UI.Web.Server.Providers.TorrentProvider import TPB, CATEGORIES, ORDERS, Torrent

from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Util import to_JSON
from UI.Web.Server.Controllers.MovieController import MovieController


class TorrentController:
    @staticmethod
    def top():
        t = TPB('https://proxyonetpb.pet/')
        result = []
        for torrent in t.top(200):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))

        return to_JSON(result)

    @staticmethod
    def search(keywords):
        t = TPB('https://pirataibay.in/')
        result = []
        for torrent in t.search(urllib.parse.unquote(keywords)).category(CATEGORIES.VIDEO).order(ORDERS.SEEDERS.DES):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))
        return to_JSON(result)

    @staticmethod
    def play_torrent(url, title):
        Logger.write(2, "Play direct link")
        url = urllib.parse.unquote_plus(url)
        url = Torrent.get_magnet_uri(url)

        EventManager.throw_event(EventType.StopTorrent, [])
        time.sleep(1)
        if url.endswith('.torrent') or url.startswith('magnet:'):
            EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url), None])
            EventManager.throw_event(EventType.PreparePlayer, ["Movie", urllib.parse.unquote(title), MovieController.server_uri, None, 0, None])
