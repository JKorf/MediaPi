import urllib.parse

from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Util import to_JSON
from Web.Server.Models import TorrentDetailModel


class TorrentController:

    @staticmethod
    def download(url, title):
        Logger.write(2, "Download torrent: " + urllib.parse.unquote(title))

        EventManager.throw_event(EventType.StartTorrent, [urllib.parse.unquote_plus(url)])

    @staticmethod
    def get_torrents(start):
        torrents = []
        if start.torrent:
            torrents.append(TorrentDetailModel.from_torrent(start.torrent))

        return to_JSON(torrents)

    @staticmethod
    def remove(start, id):
        Logger.write(2, "Remove torrent: " + id)
        start.torrent.stop()
        start.torrent = None
