import re
import urllib.parse

from bs4 import Tag
from flask import request
from bs4 import BeautifulSoup

from Shared.Network import RequestFactory
from Shared.Settings import Settings
from Shared.Util import to_JSON
from Webserver.APIController import app
from Webserver.Models import TorrentModel


class TorrentController:

    base_url = Settings.get_string("torrent_api")

    @staticmethod
    @app.route('/torrents/top', methods=['GET'])
    def top():
        category = request.args.get('category')
        if category == "TV":
            category = "television"
        elif category == "Movies":
            category = "movies"

        return to_JSON(TorrentController.get_torrents(TorrentController.base_url + "/top-100-" + category))

    @staticmethod
    @app.route('/torrents', methods=['GET'])
    def search():
        terms = urllib.parse.unquote(request.args.get('keywords'))
        category = request.args.get('category')
        return to_JSON(TorrentController.get_torrents(TorrentController.base_url + "/category-search/" + urllib.parse.quote(terms) + "/" + category + "/1/"))

    @staticmethod
    def get_magnet_url(url):
        torrent_result = RequestFactory.make_request(TorrentController.base_url + url, timeout=10)
        parsed = BeautifulSoup(torrent_result, "lxml")
        magnet_link = parsed.findAll('a', href=re.compile('^magnet:\?xt=urn:btih:'))
        if len(magnet_link) == 0:
            return None
        return magnet_link[0].attrs['href']

    @staticmethod
    def get_torrents(url):
        search_result = RequestFactory.make_request(url, timeout=10)
        if search_result is None:
            return []
        parsed = BeautifulSoup(search_result, "lxml")
        table_rows = parsed.find_all('tr')
        torrent_rows = [row.contents for row in table_rows if len([child for child in row.contents if isinstance(child, Tag) and child.name == "td" and ('name' in child.attrs['class'] or 'seeds' in child.attrs['class'])]) != 0]

        result = []
        for row in torrent_rows:
            childs = [x for x in row if isinstance(x, Tag)]
            name = [x for x in childs if 'name' in x.attrs['class']][0].text
            seeds = int([x for x in childs if 'seeds' in x.attrs['class']][0].text)
            leeches = int([x for x in childs if 'leeches' in x.attrs['class']][0].text)
            size = [x for x in childs if 'size' in x.attrs['class']][0].contents[0]
            torrent = [x for x in childs if 'name' in x.attrs['class']][0].contents[1].attrs['href']
            result.append(TorrentModel(name, seeds, leeches, size, torrent))

        return result


