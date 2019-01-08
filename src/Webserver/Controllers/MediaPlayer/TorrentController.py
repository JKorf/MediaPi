import time
import urllib.parse

from Shared.Events import EventType, EventManager
from Shared.Logger import Logger
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.BaseHandler import BaseHandler
from Webserver.Controllers.MediaPlayer.MovieController import MovieController
from Webserver.Models import TorrentModel, Media
from Webserver.Providers.TorrentProvider import TPB, Torrent


class TorrentController(BaseHandler):
    def get(self, url):
        if url == "top":
            self.write(self.top())
        elif url == "search":
            self.write(self.search(self.get_argument("keywords")))

    def top(self, ):
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.top(200):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))

        return to_JSON(result)

    def search(self, keywords):
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.search(urllib.parse.unquote(keywords)):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))
        return to_JSON(result)