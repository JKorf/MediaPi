import time
import urllib.parse

from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.Controllers.MovieController import MovieController
from Webserver.Models import TorrentModel, Media
from Webserver.Providers.TorrentProvider import TPB, Torrent, CATEGORIES, ORDERS


class TorrentController:
    @staticmethod
    def top():
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.top(200):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))

        return to_JSON(result)

    @staticmethod
    def search(keywords):
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.search(urllib.parse.unquote(keywords)):
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
            EventManager.throw_event(EventType.PreparePlayer, [Media("Torrent", 0, urllib.parse.unquote(title), MovieController.server_uri, None, None, 0)])
