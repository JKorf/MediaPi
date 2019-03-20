import urllib.parse

from flask import request

from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Controllers.MediaPlayer.TorrentProvider import TPB
from Webserver.Models import TorrentModel


class TorrentController:

    @staticmethod
    @app.route('/torrents/top', methods=['GET'])
    def top():
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.top(200):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))

        return to_JSON(result)

    @staticmethod
    @app.route('/torrents', methods=['GET'])
    def search():
        keywords = request.args.get('keywords')
        t = TPB(Settings.get_string("tpb_api"))
        result = []
        for torrent in t.search(urllib.parse.unquote(keywords)):
            result.append(TorrentModel(torrent.title, torrent.seeders, torrent.leechers, torrent.size, str(torrent.url), torrent.sub_category))
        return to_JSON(result)
